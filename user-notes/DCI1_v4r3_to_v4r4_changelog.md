# DCI-1 preregistration changelog: revision 3 → revision 4

**Current version:** 4.0 revision 4, registered 21 August 2026. **Adopted** by
the researcher on 21 August 2026 (`dci1/DECISIONS_V4R4.md` entry B0) and
registered under a signed study-wide manifest. **Not frozen; no confirmatory
data.**

**Supersedes.** 4.0 revision 3, which is **closed at Gate 1**. Revision 3 was
registered, never frozen, and produced no confirmatory data. It refused Gate 1
with `MEASUREMENT_EVIDENCE_INSUFFICIENT` under the criterion it had registered —
§18 stage 4: §10.2 *plus §10.3 or §10.4* — because neither of those two
pathways completed. That outcome stands. It is recorded at
`dci1/reports/dci1v4r3/gate1_decision.json`, summarised at
`dci1/reports/dci1v4r3/closure.json`, and **nothing in this revision changes
it**. No sentence in this document, in the v4r4 preregistration, or in any v4r4
artifact describes v4r3's Gate 1 as having passed.

**Does not touch.** DCI-1 v2 and v3 and their results. v4r2's and v4r3's signed
qualification, apparatus and regime-screen records on all four models — they
remain valid evidence *under their own rules*, are not edited, and are not
reinterpreted. v4r3's reviewer evidence (§10.3's plan, §10.4, §10.4-R,
§10.4-R2, the validator diagnosis, the defect-sensitivity analysis) — preserved
unchanged and reclassified as **supplementary / diagnostic**. The four v4r2
design screens and their frozen protocols. **No number in any of them changes.**

**Historical comparability, once, for everything below.** Neither v4r2 nor v4r3
produced a confirmatory estimate of any quantity. Every "affected results" line
therefore reads the same way: *no confirmatory result is affected because none
exists*. Two pre-confirmatory tables **do** change, and both changes are
restrictions rather than revisions: the §12.2 difficulty table and §12.6's
coverage evaluation are recomputed on a candidate population two families
smaller. Every retained rung's solo compliance, chance compliance, vacuity and
instructed compliance is **numerically identical** to v4r3's, because the
generations are the same generations and the counting predicates are
byte-identical; the change is that two families' rows are no longer in the
table. `dci1/reports/dci1v4r4/cp4_cp7_analysis.json` evaluates the coverage
criterion both ways on the same measured data and records that no condition
moves on any replication.

---

## How to read this document

Every change carries the same seven fields as the v4r2 → v4r3 changelog, in the
same order, with the same classification vocabulary: *implementation ·
measurement · treatment · design · estimator · inference · construct ·
lifecycle*.

The four changes below are not independent. R4-1 is the revision; R4-3 is the
new rule it brings; R4-2 is the first thing that rule found; R4-4 is what the
rule is allowed to conclude. Read in that order they are one change.

---

## R4-1. Gate 1's measurement criterion is deterministic, not reviewer-based

**What changed.** §18 stage 4 required

> §10.2 for every verifier in the final instrument population, **plus §10.3 or
> §10.4**; verifier hash frozen.

It now requires

> §10.2 for every verifier in the final instrument population, **plus §10.7
> A–E**; verifier hash and wording hash frozen.

§10.7 is new and has five components: **A** specification validity (an
executable formal specification per family and form, plus A′, the
prose-to-predicate invariant of R4-3); **B** implementation validity
(determinism, frozen boundary suites, adversarial and Unicode corpora); **C**
independent reimplementation from prose alone, exact agreement; **D** mutation
validation; **E** provenance and hash binding. Ten conditions, and none of them
is a reviewer-agreement threshold.

§10.3, §10.4, §10.4-R and §10.4-R2 are **reclassified as supplementary
semantic diagnostics**. They are not deleted, their recorded outcomes stand,
they travel with every v4r4 Gate-1 record under `supplementary_diagnostics`,
and no v4r4 gate reads a number out of them in either direction.

**Where.** New §10.7. Consequences for §18 stage 4, §10.5, §28.1, §29, §31.

**Why.** A registered DCI constraint is *mechanically decidable*. The pipeline
is `model response → deterministic verifier → compliance outcome`, and the
verifier's output **is** the compliance outcome by construction. There is no
latent quantity that an external rater estimates and no ground truth the
verifier approximates. So a reviewer-agreement rate measures the reviewer, and
v4r3's development record is specific about what it measured: across §10.4,
§10.4-R and §10.4-R2 — three separate designs, two of them explicitly repaired
— human and LLM reviewers introduced counting, arithmetic, segmentation,
threshold and convention errors of exactly the kind a deterministic verifier
exists to remove. §10.4-R2's own diagnosis
(`dci1/reports/dci1v4r3/validator_diagnosis.json`) is that agreement ran at
0.929→0.943 on answers with words and 0.231→0.692 on wordless ones: the
failure was **convention access**, not competence, and no amount of further
reviewing would have converged it, because the convention is a registered
definition and not a fact about the world.

Deterministic code is not automatically correct, and this revision does not
claim it is. It claims the opposite: deterministic code must be validated by
the methods appropriate to deterministic code — formal specification, executed;
independent reimplementation; adversarial and boundary corpora; and mutation
testing, which is the one that answers the question §10.2 could not. §10.2
reported 1.000 agreement between two implementations on 164 frozen cases and
700,800 verdicts. Perfect agreement is consistent with two things: the
instrument is correct, or *the suites cannot tell a correct instrument from a
broken one*. Component D separates them by requiring, for every registered
defect class, an answer on which a verifier carrying that defect would return a
different verdict.

**Classification.** *lifecycle*, with a *measurement* consequence: what counts
as measurement validity changes, though nothing about what any verifier
computes changes.

**Affected results.** No confirmatory result: none exists. v4r3's Gate-1
refusal is unaffected and unmodified.

**Comparability.** v4r3's Gate-1 record and v4r4's are decided under different
rules, and each record carries the rule it was decided under, by hash. They are
not two readings of one criterion.

**The §31 objection, registered rather than answered away.** v4r3 §31 says an
amendment is never used to weaken a criterion in order to make a gate pass, and
that a gate executed under a revision and failed gets the registered reading
rather than a further revision. This revision is adopted after v4r3's Gate 1
failed, so the objection applies to it directly. The counter-argument is
checkable rather than rhetorical and has two halves.

*It buys no stronger claim.* The measurement basis §10.7 writes is
`deterministic_measurement_validated`, which is **not** `human_validated`, so
§10.5's scope sentence — *the outcomes are verifier-defined and support no
claim about compliance as an independent human would judge it* — attaches to
every analysis record, every claim at every rung and the final report, exactly
as it would have under v4r3. §10.5's second question is as unanswered here as
it was there. A criterion whose removal licenses no additional assertion was
not standing between the study and a conclusion; it was standing between the
study and *execution*.

*It is stricter where it can be.* The specification is executed rather than
described; mutation sensitivity becomes a gate condition rather than a
diagnostic; and a prose-to-predicate invariant now runs over all 2,096
model-facing wordings, which §10.6's verifier hash never covered because a
wording cannot change what a verifier computes. The first thing that invariant
found is R4-2, and R4-2 removed two families rather than waiving anything.

A reader who weighs both halves and still prefers v4r3's reading has everything
needed to say so. The v4r3 tree is intact, its Gate-1 record is unmodified, and
`dci1/src/dci1v4r4/protocol/revision.py` names every difference.

---

## R4-2. CP4 and CP7 are removed from the candidate population (§7.0-R4)

**What changed.** The candidate library goes from 30 families and 584 declared
instruments to **28 families and 524**. `CP4` (doubled letters, rate lower
bound) and `CP7` (letter a, rate lower bound) are removed. The class arm is
`CL7`, `CL8`, `CX1`, `CX2`. `FORM_RATE_LOWER_BOUND` stays in §7.0's grammar and
in the verifier; no family instantiates it.

**Where.** §7.0 (the family table), §7.4 (the class arm), §12.3's shortlist,
§13.7's class admission. `dci1/src/dci1v4r4/verifiers/constraints.py`
`REMOVED_IN_V4R4` carries the finding on the mandatory path.

**Why.** R4-3's invariant classified two of each family's four model-facing
wordings as genuinely ambiguous:

> *"Give {q} percent of words doubled letters."*
> *"Make {q} percent of words carry doubled letters."*
> *"Give {q} percent of words letter a."*
> *"Make {q} percent of words carry letter a."*

The registered predicate is a lower bound, `100·S/W ≥ q`. Each of these states
the severity as a **target quantity** and names no bound, so the prose does not
distinguish `≥ q` from `== q`. The two readings agree on an answer at exactly
`q` and disagree on **every answer past it** — where the verifier records a
*pass*. So the instrument credits compliance to answers that one available
reading of the instruction calls non-compliant: a one-sided leniency in the
**treatment**, not in the verifier. No amount of §10.2 evidence could have
found it, because §10.2 measures agreement between two implementations of the
same predicate and both agree.

**Which remedy, and how it was chosen.** Two remedies exist: remove the
families, or rewrite the wordings and regenerate everything measured under
them. §10.2 already registers the removal rule — a family whose instrument
fails Gate 1 is removed and the coverage criterion is re-evaluated on what
remains — and the rule was applied **prospectively and outcome-safely**:
`dci1/tools/v4r4_cp47_analysis.py` reads only the §12.2 pre-screen difficulty
table (solo compliance, chance compliance, solo vacuity per rung) on each of
the four v4r3 regime records. It touches no composed cell, no `D(B←R)`, no
`Δ`, no `Ξ`; the loader it uses refuses a composed field by name before any
value is read.

The result, at `dci1/reports/dci1v4r4/cp4_cp7_analysis.json`: **C1–C6 cannot
move**, because those six conditions read rows whose role is `reference` and
both removed families are `class_control` — a property of the criterion, not an
observation about these models, and the run confirms it rather than resting on
it. **C7 holds on all four replications** without them: `gemma-3n-e2b-it` and
`gemma-3n-e4b-it` and `qwen3-4b-instruct-2507` keep `CL7`, `CL8`, `CX1` and
`CX2` inside §13.7's 0.15 caliper, and `qwen3-4b` keeps `CX1` and `CX2` — on
that model CP4 and CP7 were never in the matched set. So the removal branch
was taken.

**What removal costs, stated rather than discovered.** CP4 and CP7 were the
only families carrying the rate-lower-bound form, so the class arm is now
{count lower bound, exact count}. §7.4-R3's own argument is why that is
tolerable and not merely survivable: A is an exact-count production constraint,
and `CX1` — A's rule, A's ladder, A's four templates, over a different marker
word — is the tightest class companion the grammar can build. The families
removed here were the loosest.

**What rewriting would have cost, recorded but not decisive.** The four
wordings render at 60 severities across the two declared ranges. §12.2 spreads
four wordings over its 24 pre-screen topics, so changing a wording invalidates
the *whole* of both families' measured rows — 16 round-0 rungs × 24 topics on
each of four replications, **1,536 generations** — not only the 768 rows
carrying the two defective wordings. This is recorded because it is a real
difference between the remedies and a reader is entitled to see it. It did not
enter the decision: the decision rule reads coverage and nothing else.

**Classification.** *design* (which cells exist) and *treatment* (the defective
sentences leave the study).

**Affected results.** §12.2's difficulty table and §12.6's coverage evaluation
on all four replications, both **recomputed**. Every retained rung's numbers
are identical to v4r3's; two families' rows are gone. `ι_A` is unchanged on
every model (0.5556, 0.6667, 0.7500, 0.6250). No confirmatory result exists.

**Comparability.** v4r3's table and v4r4's are comparable rung by rung on the
28 families they share, and v4r4's is a strict restriction. A quantity computed
over "all class families" is not comparable across the boundary and should be
recomputed rather than carried.

**A finding the analysis raised that this revision does not repair.** The
leave-one-family-out sweep shows coverage is **not** robust to dropping an
arbitrary eligible reference family on three of the four replications: §12.6's
C4 requires four well-formed straddling feature groups and three models have
exactly four, so any one of them is load-bearing. The same sweep run on v4r3's
population returns the same families, so this is a property of the reference
pool that v4r3 already had and that the removal did not create. It is reported
rather than repaired, because repairing it would mean adding candidate families
after seeing a coverage result. §12.6's registered expansion draws from the
frozen reserve and remains available if the researcher judges the margin too
thin.

---

## R4-3. Every model-facing wording must expose its comparison direction (§10.7 A′)

**What changed.** A new registered invariant, checked as part of specification
validity. Every model-facing wording must either

* contain a phrase from the registered **direction lexicon** for its
  predicate's operator — `at most`, `no more than`, `not more than`, `more
  than`, `do not exceed`, `exceed`, `longer than`, `limit`, `keep`, `or fewer`,
  `or less` for `≤`; `at least`, `no fewer than`, `or more`, `minimum` for `≥`;
  `exactly` for `==` — or
* match a **documented construction** registered as entailing one direction and
  admissible for that operator.

A wording that gives only a target quantity **fails specification validation**.
A wording that names a *different* direction from its own predicate's fails as
`requires_correction`, which is the stronger finding of the two.

**The one documented construction, with its derivation.** A *requirement verb*
— `need`, `must`, `require` — is a necessity operator over the counted feature.
*"Your answer needs q words with letter a"* asserts that q such words are
necessary; necessity of q is satisfied by any answer with q **or more**, and
English does not license the converse: *"I need five"* is not falsified by
having ten, and *"needs at most"* is a contradiction rather than a redundancy.
So the construction entails `≥` and is admissible **only** where the registered
operator is `≥`. On a `≤` form it would name the opposite direction; on `==` it
would leave the upper half of the predicate unstated. Both of those fail, and
`tests_v4r4/test_revision_and_reuse.py` breaks each one to show it.

Two wordings in the final population rely on this construction and no others do:
`CL7`'s and `CL8`'s fourth templates, *"Your answer needs {q} words with letter
a."* and *"Your answer needs {q} words ending with y."*, at 28 severities each.
They are reported in full — construction, derivation, count — in
`dci1/reports/dci1v4r4/wording_review.json`, precisely because this is the
class a reader should be able to disagree with. If the researcher judges the
construction insufficiently unambiguous, the remedy is R4-2's other branch:
rewrite both templates, invalidate every row generated under them and
regenerate, at a cost of 16 rungs × 24 topics × 4 replications = 1,536
generations.

**What separates that construction from the one that failed.** `give` and
`make` are production verbs taking a quantity as their object. They assert no
necessity and entail no inequality, so a quantity under them is a *target* and
the reading is not unique. That is the whole difference between *"Your answer
needs 20 words with letter a"* and *"Give 20 percent of words letter a"*, and
it is lexical rather than stylistic.

**Where.** New §10.7 A′. Consequences for §7.5 (the wording obligations) and
for the wording hash of §10.7 E.

**Why.** An ambiguous instruction is a defect in the **treatment**, and §10.6's
canonical verifier hash never covered wordings, on the correct reasoning that a
wording cannot change what a verifier computes. It can change what the model
was asked. §10.7 E therefore binds a separate **wording hash** over all 2,096
model-facing wordings in the final population, so that a silent wording edit,
which is otherwise invisible to every downstream check, moves a hash.

**Classification.** *measurement* (what specification validity requires) with a
*treatment* consequence (R4-2).

**Affected results.** None directly. Through R4-2, the candidate population.

**The q = 1 plural findings, which do not block.** 45 wordings render as
*"Exactly 1 semicolons must appear in your answer"* and similar: the numeral is
1 and the noun it governs is plural. Classified **awkward but unambiguous** and
recorded rather than fixed. The numeral is what the verifier reads, the
mismatch is a register artefact of rendering a severity into a frozen template,
and §7.5's severity-invariance is what requires the template to be frozen. A
carries no such case — its own template already reads *"exactly 1 time"*.

---

## R4-4. The measurement basis, the stage record, and the evidence ledger

**What changed.** Three smaller things that follow from R4-1.

*The basis.* §10.5's registered bases gain
`deterministic_measurement_validated`, and v4r4's Gate 1 writes that and
nothing else. It **refuses** `human_validated`, `autorater_calibration_approved`
and `human_validation_unavailable` before it reads any evidence: the basis
names how validity was established, and a record saying `human_validated` under
this rule would be false. The reviewer-derived labels stay legal for *reading*,
because v4r3's preserved records carry them.

*The stage record.* Every v4r4 stage record carries `study_id`.
`write_stage_record` stamps it and `read_stage_record` refuses a record from
another study. v4r4 runs beside a closed v4r3 whose signed `QUALIFIED`,
`GATE_0_APPARATUS` and `REGIME_SCREEN` records exist on disk; the path and the
signing key already keep them apart, and this keeps them apart *at the point of
reading*, which is the check that still holds if a record is ever copied.

*The ledger.* Every v4r3 artifact v4r4 could have used is classified in
`dci1/reports/dci1v4r4/evidence_reuse_ledger.json` as `REUSED_UNCHANGED`,
`RECOMPUTED_FROM_EXISTING_RAW_DATA`, `INVALIDATED_AND_REGENERATED`,
`HISTORICAL_ONLY` or `NOT_APPLICABLE`, with its source hash, the reason reuse
is valid, and the v4r4 criterion it satisfies. A carried entry must carry a
finding for all seven registered invariants — verifier semantics, model-facing
prompt, instrument identity, severity, sampling regime, model and revision,
decoding configuration — and two of those are *measured* rather than asserted:
both revisions' compliance predicates are run over every instrument in v4r4's
population and every case of the frozen boundary corpus, and every constraint
sentence stored on every carried row is compared with the wording v4r4 renders
now.

**What is carried and what is not.** The **generations** are carried: the model
at its pinned revision, the same decoding, the same prompt. Every **derived
quantity** is recomputed under v4r4's canonical hash — verdicts, compliance,
vacuity, the difficulty table, coverage, the shortlist. §10.6 forbids carrying
a stale hash forward on the grounds that behaviour looks unchanged, so v4r4's
verifier hash is new (`constraints.py` changed) even though every counting
predicate is byte-identical, and the behavioural equivalence is *measured*
rather than assumed.

**One honest consequence.** v4r4's seed domain carries its study id, so the
seed a v4r4 plan derives for a carried row differs from the seed the row was
drawn under. Carried rows are therefore **not reproducible from v4r4's seed
schedule alone**; they are reproducible from v4r3's, which is preserved. The
divergence is counted on every carry note. A stage that regenerated instead
would get different draws and be a different measurement, which is exactly why
the choice between carrying and regenerating is made in the ledger.

**Nothing is `INVALIDATED_AND_REGENERATED`.** The two families whose wordings
failed were removed rather than reworded, so no v4r4 instrument exists for
their rows and no regeneration is owed. Their rows stay `HISTORICAL_ONLY`: real
generations, real v4r3 evidence, and evidence about nothing v4r4 measures.

**Classification.** *lifecycle*.

**Affected results.** None. No stored number changes.

---

## What v4r4 inherits unchanged

The research question and the interference construct (§3). The estimands — `D`,
`Δ_R`, `Δ_j`, `δ_difficulty`, `Ξ`, `Λ` and the reciprocal matrix (§11). The
hypotheses and the claim ladder L1–L5, with L5 withheld (§3.2). The four
registered replications and their pinned revisions (§5). The difficulty
coordinate: instructed compliance, with raw solo compliance reported beside it
(§13.3). The candidate-library grammar, its ladders, its frozen reserves and
the expansion rule (§7.0, §12.6), minus the two families of R4-2. Every
registered threshold, caliper, band and precision precondition (§12, §13, §16,
§11.8). The topic bank, its five sets and the reservation rule (§6.2, §12.5).
The masking principle and the one-shot unmasking rule (§14, §17). The
confirmatory analysis plan, the bootstrap and the multiplicity correction (§15,
§17). The counting statistics, the segmentation convention and the compliance
predicates (§7.3, §9.2) — byte-identical. §10.2's evidence architecture in
full.

`dci1/src/dci1v4r4/protocol/revision.py` holds this list as data, and
`tests_v4r4/test_revision_and_reuse.py` asserts that every difference from v4r3
is enumerated there.
