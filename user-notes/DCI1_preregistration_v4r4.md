# DCI-1 preregistration — version 4.0, revision 4

**Status.** Registered 21 August 2026. **Adopted** by the researcher on 21
August 2026 (`dci1/DECISIONS_V4R4.md` entry B0) and registered under a signed
study-wide manifest. **Not frozen; no confirmatory data.**

**This is a revision document.** It restates in full only the sections v4r4
changes, and **incorporates by reference** every other section of
[`DCI1_preregistration_v4r3.md`](DCI1_preregistration_v4r3.md), which remains
the substantive protocol: the research question, the estimands, the hypotheses,
the claim ladder, the model set, the topic bank, the design, the difficulty
coordinate, the candidate-library grammar, every threshold and caliper, the
masking principle, and the confirmatory analysis plan. A section not restated
below is v4r3's, unchanged, and reads as though printed here. Both documents
are hashed into v4r4's protocol hash, so an edit to either after a v4r4 stage
record exists is visible as a hash that no longer matches.

**What v4r4 supersedes, and what it does not.** It supersedes v4r3
prospectively. It does **not** reinterpret v4r3's outcome: v4r3 refused Gate 1
with `MEASUREMENT_EVIDENCE_INSUFFICIENT` under the criterion registered at the
time, that record stands unmodified, and no sentence in this document or in any
v4r4 artifact describes it as having passed. The change-by-change account is
[`DCI1_v4r3_to_v4r4_changelog.md`](DCI1_v4r3_to_v4r4_changelog.md).

**The causal history, stated once.**

> v4r3 failed Gate 1 under reviewer-based validation → development evidence
> showed that validation architecture was poorly matched to mechanically
> decidable constraints → before Gate 2 and before any confirmatory scientific
> outcome was observed, v4r4 prospectively adopted deterministic specification
> and implementation validation → v4r4 was evaluated under that rule from
> scratch.

---

## What this revision changes

| id | section | change |
|---|---|---|
| R4-1 | §18 stage 4, new §10.7 | Gate 1's measurement criterion becomes deterministic specification and implementation validation. §10.3/§10.4 become supplementary diagnostics |
| R4-2 | §7.0-R4 | `CP4` and `CP7` are removed from the candidate population on a specification-ambiguity finding. 28 families, 524 declared instruments |
| R4-3 | §10.7 A′ | every model-facing wording must expose the comparison direction of the predicate that scores it |
| R4-4 | §10.5, §18, §26 | the measurement basis `deterministic_measurement_validated`; `study_id` on every stage record; the v4r3 → v4r4 evidence ledger |

Everything else is v4r3's. `dci1/src/dci1v4r4/protocol/revision.py` carries the
same list as executable data, and `tests_v4r4/test_revision_and_reuse.py`
asserts that a difference not enumerated there is a defect.

---

## 7.0-R4 The candidate population loses two families

`CP4` (doubled letters, rate lower bound) and `CP7` (letter a, rate lower
bound) are **removed**. The candidate library is **28 families and 524 declared
instruments**; the class arm is `CL7`, `CL8`, `CX1`, `CX2`.
`FORM_RATE_LOWER_BOUND` remains in §7.0's grammar and in the verifier, and no
family instantiates it.

**The finding.** Two of each family's four model-facing wordings —

> *"Give {q} percent of words doubled letters."* ·
> *"Make {q} percent of words carry doubled letters."* ·
> *"Give {q} percent of words letter a."* ·
> *"Make {q} percent of words carry letter a."*

— state the severity as a target quantity and name no bound, while the
registered predicate is a lower bound, `100·S/W ≥ q`. The prose does not
distinguish `≥ q` from `== q`. The readings agree on an answer at exactly `q`
and disagree on **every answer past it**, where the verifier records a *pass*:
the instrument credits compliance to answers that one available reading of the
instruction calls non-compliant. That is a one-sided leniency in the treatment,
it fails §10.7 A′, and it is not waivable.

**The rule that permits removal.** §10.2 registers it: a family whose
instrument fails Gate 1 is removed from the candidate population and §12.6's
coverage criterion is re-evaluated on what remains. The re-evaluation was done
**before** the removal was taken and **outcome-safely** — it read only the
§12.2 pre-screen difficulty table (solo compliance, chance compliance, solo
vacuity per rung) on the four v4r3 regime records, and no composed cell, `D`,
`Δ` or `Ξ`. `dci1/reports/dci1v4r4/cp4_cp7_analysis.json` is the artifact.

**The result.** C1–C6 read rows whose role is `reference`; both removed
families are `class_control`, so those six cannot move on any table — a
property of the criterion, confirmed by the run rather than assumed. C7 holds on
all four replications: three keep `CL7`, `CL8`, `CX1` and `CX2` inside §13.7's
0.15 caliper, and `qwen3-4b` keeps `CX1` and `CX2`, on which model the removed
families were never in the matched set. `ι_A` is unchanged on every model.

**What is lost, stated rather than discovered.** These were the only two
rate-lower-bound families, so the class arm is now {count lower bound, exact
count}. §7.4-R3's own argument is why that is tolerable: A is an exact-count
production constraint, and `CX1` — A's rule, A's ladder, A's four templates,
over a different marker word — is the tightest class companion the grammar can
build. The families removed here were the loosest.

**Registered limitation, carried forward.** The leave-one-family-out sweep in
the same artifact shows §12.6's C4 is satisfied with no margin on three of the
four replications: exactly four well-formed straddling feature groups, so any
one is load-bearing. The same sweep on v4r3's population returns the same
families, so the removal did not create this. It is recorded and not repaired,
because repairing it would mean adding candidate families after seeing a
coverage result. §12.6's registered expansion draws from the frozen reserve and
remains available.

---

## 10.5 The measurement basis (amended)

§10.5's three questions and its scope sentence are unchanged and are still
never aggregated. The registered bases gain one entry:

`deterministic_measurement_validated`
: written by a Gate 1 that passed §10.7 A–E. It is **not** `human_validated`,
  so §10.5's scope sentence attaches to every analysis record, every claim at
  every rung and the final report, permanently, and no later stage may remove
  it.

v4r4's Gate 1 writes that basis and refuses every other. `human_validated`,
`autorater_calibration_approved` and `human_validation_unavailable` remain
legal *labels*, because v4r3's preserved records carry them and a reader must
be able to place one; no v4r4 stage can write any of them. The refusal happens
before the gate reads any evidence: the basis names how validity was
established, and a record claiming `human_validated` under this rule would be
false.

---

### 10.7 Deterministic-measurement validation

**Exactly what this replaces, and in which revision.** v4r3's §18 stage 4
read: *§10.2 for every verifier in the final instrument population, **plus
§10.3 or §10.4**; verifier hash frozen.* v4r4's reads: *§10.2 for every
verifier in the final instrument population, **plus §10.7 A–E**; verifier hash
and wording hash frozen.* §10.3 and §10.4, with §10.4-R and §10.4-R2, are
retained in full, are **supplementary / diagnostic** under this revision, and
are not Gate-1 prerequisites. Nothing about them is deleted, rewritten, or
re-scored.

**When this was registered, and what had been seen.** Registered 2026-08-21,
before any v4r4 stage record existed, before Gate 2, and before any freeze or
confirmatory generation in either revision. All four replications stood at
`REGIME_SCREEN`; no `gate1_measurement.json` existed anywhere in the v4r3 tree
or in v4r4's; no composed cell had been generated; no estimand had been
computed; no mask had been built and nothing had been unmasked. What *had* been
seen was §10.2 complete over v4r3's final population, §10.4-R2's development
half returning FAIL on its registered criterion 5, and the §10.3 pathway
standing at `HUMAN_VALIDATION_UNAVAILABLE` for want of an annotator independent
of the design and analysis team. The scientific estimands were, and remain at
registration, unseen.

**v4r3's Gate 1 is not re-read by this section.** v4r3 refused Gate 1 with
`MEASUREMENT_EVIDENCE_INSUFFICIENT` under the criterion registered at the time.
That record stands unmodified at
`dci1/reports/dci1v4r3/gate1_decision.json`, its closure is recorded at
`dci1/reports/dci1v4r3/closure.json`, and nothing here describes it as having
passed. v4r4's Gate 1 is a new evaluation under a different rule, run from
scratch, and each record carries by hash the rule it was decided under.

**The §31 tension, recorded rather than resolved quietly.** v4r3 §31 says an
amendment is never used to weaken a criterion in order to make a gate pass, and
its second consequence says that if a gate is executed and fails, the answer is
the registered reading and not a further revision. This revision is adopted
*after* §10.4-R2 failed and *because* the accumulated evidence around that
failure changed the researcher's view of what §10.3 and §10.4 were measuring. A
reader is entitled to hold that §31 forbids it and that halting was the
registered answer; that reading is recorded here as a live objection and is not
argued away.

What is offered against it is one fact, and it is checkable rather than
rhetorical: **this revision buys no stronger claim.** Under `human_validated`
the study could have dropped §10.5's scope sentence. Under the basis §10.7
creates, the scope sentence attaches permanently and unconditionally, at every
rung, in every analysis record, and in the final report, and no later stage may
remove it. The three questions of §10.5 stay separate and question 2 — *can an
independent human reproduce it?* — stays **unanswered**, exactly as it was
before. v4r4 therefore changes whether the study executes, not what the study
may assert. A criterion whose removal cannot strengthen any claim is not a
criterion that was standing between the study and a conclusion.

The second half of the answer is that the replacement is **stricter where it
can be**: the specification is executed rather than described, mutation
sensitivity becomes a gate condition rather than a diagnostic, and A′ below
runs a prose-to-predicate invariant over every model-facing wording — which
§10.6's verifier hash never covered. The first thing that invariant found was a
defect in the treatment that three rounds of reviewing had not surfaced, and
§7.0-R4 removed the two families carrying it rather than waiving it.

**Why external agreement is the wrong mandatory criterion for these
instruments.** For the registered constraints, compliance is a mechanically
decidable property of the response string: exact counts, upper and lower
bounds, percentages of a word denominator, segmentation, punctuation counts and
word-length rules. The chain is *model response → deterministic verifier →
compliance outcome*, and the verifier is the definition of the outcome, not an
estimator of a latent human judgement. Against that construct the accumulated
development evidence says:

- the primary verifier and the prose-only independent reimplementation agree
  exactly, on every counted statistic on every stored response and on the full
  verdict vector over the declared sample;
- three-process determinism is exact;
- the boundary, Unicode, adversarial, witness and wording suites are extensive
  and are frozen;
- defect sensitivity shows that several implementation mistakes would move a
  material share of labels, so the suites are testing something that could
  fail;
- human and LLM reviewers themselves make exactly the errors the deterministic
  verifier exists to avoid — miscounting, denominator confusion, threshold
  direction, off-by-one, and segmentation — and §10.4-R2's own failure is
  attributable to a registered stipulation the deciding arm withheld rather
  than to any inability to check the verifier;
- some registered defects cannot be detected on natural responses at all,
  because the discriminating case does not occur there; absence of natural
  counterexamples is not agreement, and an agreement rate computed on natural
  responses silently reports it as if it were.

Therefore raw reviewer agreement is not an appropriate gold standard for these
predicates. **This does not imply that deterministic code is automatically
correct.** A deterministic verifier can implement the wrong predicate perfectly,
and a prose instruction can fail to pin down which predicate was meant. Those
are the two failure modes that matter, and A–E below are built to test them
directly rather than through a proxy.

#### The two questions the amended Gate 1 answers

1. **Specification validity.** Does the written constraint correspond
   unambiguously to the intended formal predicate?
2. **Implementation validity.** Does the deterministic verifier correctly and
   reproducibly implement that predicate?

#### A. Specification audit

For every distinct family and predicate form in the final instrument
population, a specification record carries: the exact natural-language
instruction templates as the model receives them; the full-prose rule
statement; the counted statistic and what it counts; the segmentation
convention; the numerator definition; the denominator definition, or the
explicit statement that the form has none; the comparison operator; the
threshold and severity interpretation; the zero-denominator and vacuity rule;
the case-folding and Unicode behaviour; and the **exact formal predicate** in a
machine-evaluable form.

The audit is decided by deliberately constructed discriminating examples, never
by statistical reviewer agreement. Each family carries constructed cases at
$q-1$, $q$ and $q+1$; a zero statistic; an empty answer; a wordless answer; a
punctuation boundary; a Unicode boundary; a case-folding boundary; and, where
the form has one, a malformed delimiter. Each case records the registered
verdict and the verdict each of the six alternative readings — `inequality_flip`,
`off_by_one`, `numerator_swap`, `denominator_swap`, `segmentation_drift`,
`vacuity_ignored` — would record.

Three checks decide the audit, and all three are executable:

1. **Completeness.** Every field above is present and non-empty for every
   family and form in the final population.
2. **Prose-to-predicate correspondence.** The recorded formal predicate,
   evaluated by a generic evaluator that reads only the specification record,
   reproduces the primary verifier's verdict on every constructed case and on
   the entire frozen boundary corpus. The specification record is therefore
   itself under test: a predicate that is merely described cannot pass, only
   one that can be executed from what is written down.
3. **Resolution of alternative readings.** For every alternative reading that
   is *meaningful* for the form, the specification record names it, states
   which reading is registered, and points at a constructed case that separates
   them. A reading that cannot be meaningful for a form — a denominator swap in
   a form with no denominator, a segmentation drift in a statistic that reads
   raw characters — is recorded as *not applicable with its reason*, and
   silence is never accepted for either.

An unresolved ambiguity fails Gate 1. That is not softened anywhere in this
amendment.

#### A′. The prose-to-predicate invariant, and the wording review

The wording a model receives is audited separately from implementation
correctness, because a defect there is a defect in the treatment and not in the
verifier, and §10.2 is structurally unable to see it: it measures agreement
between two implementations of the same predicate, and both agree whatever the
prose says.

**The invariant.** Every model-facing wording must expose the comparison
direction of the predicate that scores it. A wording satisfies this if it
contains a phrase from the registered **direction lexicon** for its operator —

| operator | registered phrases |
|---|---|
| `≤` | at most · no more than · not more than · more than · do not exceed · exceed · longer than · limit … to · keep … to · or fewer · or less |
| `≥` | at least · no fewer than · or more · minimum |
| `==` | exactly |

— or if it matches a **documented construction** registered as entailing one
direction and admissible for that operator. **A wording that expresses a
directional predicate only as a target quantity, with no operator, fails
specification validation.** A wording that names a direction other than its own
predicate's fails as *requires correction*, which is the stronger of the two
findings.

**Documented constructions.** One is registered, and its scope is deliberately
narrow. A **requirement verb** — *need*, *must*, *require* — is a necessity
operator over the counted feature: *"your answer needs q words with letter a"*
asserts that q such words are necessary, and necessity of q is satisfied by any
answer with q **or more**. English does not license the converse reading:
*"I need five"* is not falsified by having ten, and *"needs at most"* is a
contradiction rather than a redundancy. The construction therefore entails `≥`
and is admissible **only** where the registered operator is `≥`; on a `≤` form
it names the opposite direction, and on `==` it leaves the upper half of the
predicate unstated. A construction reaches this table by having its entailment
written down and checked, never by being convenient, and every wording that
relies on one is reported in full — which construction, which derivation, how
many severities — because that is the class of finding a reader should be able
to disagree with.

The rule is exhaustive over the population by assertion, not by hope: a wording
matching neither the lexicon nor a documented construction is reported by
family, severity and wording index, and blocks. Adding a wording that names its
direction some new way therefore surfaces as a finding rather than passing
silently.

**The rest of the review.** Every wording of every family at every severity of
the declared range is additionally classified as **mechanically awkward but
semantically unambiguous**, **genuinely ambiguous**, or **misleading enough to
require correction**. The singular/plural mismatch at $q = 1$ — *"Exactly 1
semicolons must appear in your answer"* and its analogues — is audited by name,
and is awkward rather than ambiguous: the numeral is what the verifier reads,
and the mismatch is a register artefact of rendering a severity into a template
that §7.5's severity-invariance requires to be frozen.

Live prompt wording is never silently fixed. If a wording is judged
scientifically defective and must change, the change is registered
prospectively; every affected family and rung is identified; every downstream
solo, regime and screen measurement that depended on that wording is invalidated
and recorded as invalidated; and the necessary pre-confirmatory stages are
rerun. **Coverage measured under one wording is never carried across a changed
wording.** The wordings of the final population are hashed and that hash is
bound into the Gate-1 record (E), so a wording change is detectable rather than
asserted.

#### B. Deterministic implementation validation

§10.2 is retained unchanged and mandatory, over the **final** instrument
population: cross-process determinism; canonical source hash; the frozen
boundary suite; the adversarial and fuzz corpus; Unicode and segmentation
differential checks; exact threshold cases; satisfiability and non-entailment
witnesses; wording-equivalence checks; reproducibility on stored responses; and
the carry-over record. Any disagreement between the primary and independent
implementations is adjudicated **against the formal specification of A**, never
by majority vote and never by which implementation is more convenient.

#### C. Independent reimplementation

The prose-only reimplementation of §10.2 remains mandatory and remains an
instrument under test in its own right, including the whole-Unicode segmenter
differential. Zero unexplained disagreement is required. An explained
disagreement is one adjudicated under B against A's specification and recorded
with its adjudication.

#### D. Adversarial, boundary and mutation validation

The adversarial corpus of §24 remains mandatory. **Mutation testing becomes an
explicit Gate-1 requirement.** For each of the six registered defect classes,
the evidence must show that the frozen suites and A's constructed cases contain
at least one case that *discriminates* the registered reading from the
defective one — that is, a case on which applying the defect changes the
recorded verdict — for every family and form where that defect is meaningful.
Sensitivity is reported by family and form.

A defect that cannot occur for a particular form is not forced into it, but
**this must be explicit**: the report names the family, the defect, and the
reason it cannot occur, and an unexplained absence is a failure, not a pass.

The defect-sensitivity analysis on observed natural responses is retained and is
used **only** to establish practical consequence on real data. It is never read
as semantic validation, and where it shows that a defect changes no natural
label — as `vacuity_ignored` does — the correct reading is that the natural
corpus cannot validate that convention, not that the convention was validated.

#### E. Provenance and hash binding

The Gate-1 record binds: the canonical verifier hash of §10.6; the hash of the
frozen boundary suite; the hash of every model-facing wording in the final
population; the hash of the specification audit; the hash of the mutation
report; the measurement-rule hash of this subsection; the v4r4 protocol hash; the producing commit; and the
environment digest. Every downstream entry point re-verifies the verifier hash
as §10.6 already requires, and additionally refuses on a wording-hash mismatch.

#### The Gate-1 rule

Gate 1 passes if and only if **all ten** of the following hold.

1. Every family and form in the final instrument population carries a complete
   formal specification record (A.1).
2. The specification audit finds no unresolved prose-to-predicate ambiguity
   (A.2 and A.3).
3. The primary verifier is deterministic: three processes, agreement exactly
   1.000.
4. The independent reimplementation agrees exactly on the registered validation
   corpus, with zero unexplained disagreement.
5. Every required boundary, adversarial and Unicode test passes, and the
   boundary corpus meets its registered minimum size.
6. Mutation tests demonstrate sensitivity to every registered defect class
   wherever that class is meaningful, with every non-applicability explained.
7. The satisfiability and non-entailment witness requirements pass.
8. The wording-equivalence requirements pass, every model-facing wording in
   the final population exposes its comparison direction under A′, and the
   wording review records no wording classified as genuinely ambiguous or as
   requiring correction.
9. The canonical verifier hash and the wording hash are bound correctly and
   match the evidence they certify.
10. Lifecycle and provenance integrity passes: the predecessor record verifies,
    the carry-over record refuses on any mismatch, and reserved sets are unspent.

**No human or autorater agreement rate, sample size, Wilson bound, accuracy,
repeatability or judge verdict appears in this rule.** Reviewer
evidence is carried in the record as a diagnostic and cannot cause a pass or a
failure. Equally, reviewer evidence never overrides a formally specified
deterministic predicate: a reviewer who miscounts, applies the wrong
denominator or flips a threshold has produced a finding about the wording or
about the reviewer, and the mechanism for acting on it is A′ or a registered
verifier change under §10.2 and `CHANGES_SCIENTIFIC.md`, never a re-labelling
of the outcome.

#### The measurement basis this creates, and what it never licenses

A Gate-1 pass under this rule writes `measurement_basis =
deterministic_measurement_validated`. That basis is not `human_validated`,
and §10.5's scope sentence therefore attaches to every analysis record, every
claim at every rung, and the final report: *the outcomes are verifier-defined
and support no claim about compliance as an independent human would judge it.*
No later stage may remove it. The basis may never be upgraded except by new
evidence of the kind §10.3 or §10.4 specifies, produced under those sections'
own criteria.

§10.5's three questions are unchanged and are still never aggregated. §10.7
answers question 1 more thoroughly than §10.2 alone did, by adding the
specification half. It does not answer question 2 and does not claim to. It
does not touch question 3.

#### Reclassification of the external-review sections

§10.3, §10.4, §10.4-R and §10.4-R2, the 25 author-performed annotations, the
frozen §10.3 sampling plan, and any future optional human check are
**supplementary semantic diagnostics**. They may reveal confusing wording,
undocumented assumptions, presentation problems and specification ambiguity,
and a finding of that kind is actionable under A′ or under §10.2. They are
preserved unchanged and remain readable under their own recorded hashes. Their
recorded outcomes stand: §10.4-R2 **FAILED** and its stopping rule took effect;
§10.3 stands **unavailable**. Neither is described anywhere as having succeeded,
and a Gate-1 pass under this rule is never described as a retroactive pass of
either.

#### What would falsify this architecture

An independent annotator, later, disagreeing with the verifier at a rate §10.3's
bound would have rejected, on items where the disagreement is about the
predicate rather than about arithmetic. §10.7 does not close that door: the frozen
§10.3 plan stays unspent, and a completed §10.3 supersedes this basis rather
than being blocked by it.

#### Registered limitation

The specification audit certifies each family at the audited severities and
relies on the severity-invariance of the wordings and predicates that §7.5
establishes; it does not re-audit every rung of every ladder independently. The
prose-to-predicate check reads the same registered counting functions the
verifier reads, so it tests the mapping from prose to predicate and not the
counting functions themselves; those are covered by B, C and D.

---

## 18 stage 4, amended

| stage | gate | criterion | terminal statuses |
|---|---|---|---|
| 4 | `GATE_1_MEASUREMENT` | §10.2 for every verifier in the final instrument population, **plus §10.7 A–E**; verifier hash **and wording hash** frozen. *v4r3's criterion was §10.2 plus §10.3 or §10.4* | `MEASUREMENT_NOT_ESTABLISHED`, `MEASUREMENT_EVIDENCE_INSUFFICIENT`, `SPECIFICATION_AMBIGUOUS` |

`SPECIFICATION_AMBIGUOUS` is a distinct terminal status because it names a
defect in the **specification**, which no amount of implementation evidence can
repair. Every other stage in §18's table is v4r3's, unchanged.

**Two additions to §18's machine.** Every stage record carries `study_id`;
`write_stage_record` stamps it and `read_stage_record` refuses a record whose
`study_id` is not this study's. v4r4 runs beside a closed v4r3 whose signed
`QUALIFIED`, `GATE_0_APPARATUS` and `REGIME_SCREEN` records exist on disk, and
none of them may satisfy a v4r4 predecessor check. The path and the signing key
already keep them apart; this keeps them apart at the point of reading, which
is the check that still holds if a record is ever copied.

---

## 26-R4 The evidence reuse and invalidation ledger

Evidence produced under v4r3 may enter v4r4 **only** through an explicit
ledger, at `dci1/reports/dci1v4r4/evidence_reuse_ledger.json`. Every relevant
artifact carries exactly one classification —

`REUSED_UNCHANGED` · `RECOMPUTED_FROM_EXISTING_RAW_DATA` ·
`INVALIDATED_AND_REGENERATED` · `HISTORICAL_ONLY` · `NOT_APPLICABLE`

— together with its source artifact, its source hash, the reason reuse is
scientifically valid, and the v4r4 criterion it satisfies. An entry in either
of the two carrying classes must record a finding for **all seven** registered
invariants: verifier semantics, the model-facing prompt, instrument identity,
severity, the sampling regime, the model and its revision, and the decoding
configuration. Two of the seven are *measured* rather than asserted — both
revisions' compliance predicates are run over every instrument in v4r4's
population against every case of the frozen boundary corpus, and every
constraint sentence stored on every carried row is compared with the wording
v4r4 renders now.

**What is carried is generations; what is recomputed is everything derived
from them.** The model at its pinned revision, the decoding configuration and
the rendered prompt determine a generation, and none of those changed for the
28 families v4r4 carries. Verdicts, compliance rates, vacuity, the §12.2
difficulty table, §12.6's coverage and §12.3's shortlist are all computed again
under v4r4's canonical verifier hash. §10.6 forbids carrying a stale hash
forward on the grounds that behaviour looks unchanged, so v4r4's verifier hash
is new and the behavioural equivalence is measured.

**One consequence, recorded rather than hidden.** v4r4's seed domain carries
its study id, so a carried row's scientific seed is v4r3's and not the one
v4r4's plan would derive. Carried rows are reproducible from v4r3's seed
schedule, which is preserved, and not from v4r4's alone. The divergence is
counted on every carry note, and a stage record that rests on carried rows says
so on its face.

**Do not rerun expensive work to produce a fresher timestamp; do rerun anything
whose determinants changed.** Both halves are enforced by the same ledger.

---

## 29-R4 Registered limitations added by this revision

Three, in addition to v4r3's, which stand unchanged.

**The measurement claim is verifier-defined and stays that way.** §10.7
establishes that the instrument implements the predicate the prose specifies.
It does not establish that an independent human would reproduce the verdicts,
and it does not claim to. §10.5's scope sentence attaches to every claim under
this basis. A completed §10.3, later, supersedes this basis rather than being
blocked by it, and the frozen §10.3 sampling plan stays unspent.

**This revision was adopted after the criterion it replaces had failed.**
§10.7's own text records the §31 objection and the checkable answer to it. A
reader who weighs both and prefers v4r3's reading has an intact v4r3 tree and
an unmodified Gate-1 record with which to say so.

**The class arm carries no rate lower bound.** §7.0-R4's removal leaves the
class pool at {count lower bound, exact count}. §13.7's class contrast is
therefore bounded by companions of two forms rather than three, and the
strongest of them, `CX1`, is A's own form — which is the point of the arm, and
also the reason the loss is tolerable rather than merely survivable.

---

## 31-R4 Amendment discipline under this revision

v4r3 §31 is carried in full and applies to v4r4 exactly as it applied to v4r3.
Two consequences are restated because this revision is the case they govern.

**An amendment is never used to weaken a criterion in order to make a gate
pass.** §10.7's text records the objection that v4r4 is such a case, and
answers it with a fact a reader can check rather than an argument: the basis
§10.7 writes is not `human_validated`, so no claim available under it was
unavailable before. What changed is whether the study runs, not what it may
say.

**A gate executed and failed gets the registered reading.** v4r3's Gate 1 has
its registered reading, it is recorded, and it is not revisited. v4r4's Gate 1
is a separate evaluation of a separate population under a separate rule, and
each record binds the rule it was decided under by hash. If v4r4's Gate 1
fails, the answer is v4r4's registered reading — not a v4r5.

**No Gate-1 measurement rule changes after Gate 2 begins.** The rule above is
final for this revision from the moment the first v4r4 Gate-1 record exists.
