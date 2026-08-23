# DCI-1 v5 — document reconciliation

Every discrepancy found while implementing v5 in `dci1/src/dci1v5/`, classified
as the implementation prompt requires: **stale documentation**, **unresolved
scientific choice**, **implementation defect**, or **true protocol
contradiction**. Stale documentation and implementation defects were fixed;
the other two are escalated here and nothing was silently edited to make
documents agree.

**No threshold, band, count or rule moved.** Every fix below is a name, a
cross-reference or a stale value that contradicted its own neighbour.

---

## 1. Stale documentation — fixed

| # | Where | What it said | What it says now | Why the change is safe |
|---|---|---|---|---|
| S1 | `DCI1_v4r4_to_v5_changelog.md` §14 | "v5 §34 carries **fourteen** registered open decisions" | nineteen, D0 to D18 | §34's own table lists D0–D18 and says "all nineteen"; the changelog was written against an earlier draft |
| S2 | same, D4 bullet | the eight markers were "chosen on three prospective rules, **none of them measured on any model**" | two of the three rules **are** measured on the predecessor study's unconstrained responses; what is not measured is any marker's behaviour *as a constraint* | §7.6 rule 3 and §7.10's table quote measured occurrence rates per marker; the unmeasured thing is the difficulty coordinate, which §6.2 states separately |
| S3 | `reference_design_spec.json` `what_this_spec_does_not_decide[0]` | "section 33 leaves as a researcher decision" | section 34, decision D1 | §33 is the red-team checklist; §34 is the open decisions |
| S4 | same, `support_requirements` | key named `terminal_status_when_unmet` | `status_when_unmet`, plus `status_when_unmet_is_terminal: false` and a note naming D6 and R16 | §13.15 says in terms that `REFERENCE_SUPPORT_NOT_IDENTIFIED` is "an identification status, **not** a stage-terminal one"; the key name contradicted the value's own meaning. §13.1: the preregistration governs and the file is repaired |
| S5 | same, `structural_taxonomy.tiers` | Tier 1's `eligible_slots` included `class_same_form` | `core_reference`, `spectrum` | no slot of that name exists anywhere; §7.4's slot table registers four |
| S6 | same, Tier 3 | `eligible_slots: [spectrum, broad_class_control]` | `broad_class_control`, with a note | see the escalation P1 below: no rule can put a Tier-3 family in a spectrum slot |
| S7 | same, `tier2_near_form_families` | statistic `comma_character` | `comma` | the registered statistic identifier is `comma`; §7.6 names it |
| S8 | `DCI1_preregistration_v5.md` §7.6 | the registered marker statistics were listed as `marker_thus, marker_hence, marker_indeed, marker_namely, **marker_notably**, marker_overall, marker_instead, **marker_finally**` | `marker_thus, marker_hence, marker_though, marker_whereas, marker_indeed, marker_namely, marker_instead, marker_overall` | §7.6's own rule 3 **rejects** `finally` at 0.185, and §7.10's registered table carries `though` and `whereas` with `notably` as a *reserve* marker. The list contradicted the two paragraphs beside it |

---

## 2. Under-specification — one reading implemented, recorded here

None of these is a contradiction; each is a rule the preregistration states
without saying how to compute one of its terms. In every case exactly one
reading is executable, the implementation takes it, and the code says so where
it is taken.

### U1. §13.8's discourse-role spread, and what a Tier-2 member contributes

§13.8 requires the three core references to "span at least two declared
discourse roles" and describes a substitution when "the three otherwise-chosen
references share one role". §7.6 assigns a discourse role to **marker**
families and to no others, so a Tier-2 member has none — and §13.8 does not
say what it contributes to the count.

**Implemented:** `none` is not a role. `protocol/taxonomy.declared_roles`
counts only members that declare one. §13.15 guarantees at least two Tier-1
members, so at least two members always declare a role and the requirement is
always well defined under this reading.

**The alternative** — counting `none` — would let a set of two same-role
markers and one Tier-2 control satisfy a rule written to make the pool span
discourse function. `assert_core_set_structure` records both the counted set
and the set as declared, so a reader can see which reading produced the
verdict.

### U2. §11.8's tier-indicator secondary fit is not identified as written

§11.8 registers `Y = alpha_f + beta*d + gamma*1[Tier 2]` over twelve points
and does not say what `alpha_f` is for the three near-form controls. Giving
each of them its own family intercept makes `gamma` **exactly collinear** with
the sum of those three dummies: the design matrix is singular and `gamma`
identifies nothing.

**RESOLVED at A2 on 2026-08-23**, by the researcher, recorded in
`researcher_decisions.json` under `open_items`. `alpha_f` ranges over the three
**core** families, and a Tier-2 point sits at the unweighted mean core
intercept plus `gamma`, so `gamma` is the tier's offset from the difficulty
line the core families define, at equal weight over them. The fit is five
parameters over twelve points and full rank.

This was **not** an implementation reading that got ratified. It was recorded
as `RESEARCHER_DECISION_REQUIRED` and `fit_with_tier_indicator` refused
outright — including when a caller named a formulation explicitly — because the
four repairs estimate different `gamma`s. It still refuses if the resolution
goes away, rather than falling back to A2: `adopted_formulation()` reads the
open-item registry, so adoption is a fact about the record and not a default in
a signature. A1 is refused by name as singular; A3 is never constructed,
because it deletes F8's registered `gamma_tier`; A4 is constructed and
**non-adopted**, kept because the decisive comparison in
`u2_tier_model_decision.md` is computed from it on every test run, and refused
on any reporting path by `assert_adopted_formulation`. §11.8's sentence is
amended to name the three core families explicitly, which is the amendment this
entry recorded as outstanding. `gamma` is an F8 secondary and licenses no
claim, so the resolution changes no decision rule.

### U3. "The less restrictive severity breaks an exact within-family tie"

§13.8 states the tie-break and leaves the word to the form. For a budget
(`<=`) a larger q admits more answers; for a lower bound (`>=`) and for an
exact count (`==`) a smaller q does — and §7.10 states the exact-count
direction in its own words: *"Higher q is harder, so extending the reserve
extends the span downward in iota"*.

**Implemented:** `stages/selection.restrictiveness_key`, derived from the
family's form. The same function fixes §12.6's expansion direction, which a
severity-value reading would have sent the wrong way for a marker ladder —
into the *non*-deficient side §7.10 widened the reserve to reach.

---

## 3. True protocol tension — escalated, nothing edited in the preregistration

### P1. §7.10 admits Tier 3 "to the spectrum"; §7.4 and §13.12 make that unreachable

§7.10 says the twenty-six Tier-3 families are "admissible to the spectrum and
to the broad-class slot only". §7.4's slot table says a spectrum rung's
admissible tier is "the tier of its own core family, because §13.12 draws both
rungs from that same family", and §7.4 admits Tier 1 and Tier 2 to the core
slot alone.

Both cannot be exercised: a Tier-3 family can never supply a spectrum rung,
because a spectrum rung belongs to an admitted **core** reference's family and
no Tier-3 family can be one.

**Operationally the two agree** — under either reading no Tier-3 rung reaches
the spectrum — so this changes no verdict, and the implementation follows §7.4
and §13.12, which are the rules with an executable form
(`assert_tier_admits_slot` requires the core family's tier for that slot).
It was escalated rather than fixed because narrowing §7.10's sentence is a
scientific edit that the researcher should make, and because the sentence is
the only place a reader would learn that a Tier-3 spectrum was ever
contemplated.

**CONFIRMED on 2026-08-23.** The researcher confirmed the corrected wording:
Tier 1 and Tier 2 take the core, near-form and spectrum roles the adopted
design gives them; Tier 3 takes the broad-class role only and does not become a
core-family spectrum rung. Nothing executable changed and no verdict moved.
Making Tier 3 *reachable* instead would amend the candidate population, §11.8's
three-families-of-three fit structure and the derived cell set — a §32
amendment — and it was not made. The consequence the corrected sentence owns
stands: `CL7` and `CL8` are count lower bounds, §13.10 admits budget class to
the broad-class slot only, and with the spectrum closed to Tier 3 they are
admissible to no design slot. They remain in the instrument population §10.2
measures.

---

## 4. Findings the implementation produced, which are not discrepancies

### F1. §7.7's realistic-witness rule finds four unreachable rungs, not two

§7.7 names `CL7:130` and `CL7:140` as formally satisfiable and unreachable
inside the 60–120 word stem band. Computed over the whole declared range
against B at every admissible severity,
`verifiers/realistic_witness.run_realistic_suite` finds **`CL7:125`, `130`,
`135` and `140`** and nothing else in the library. The general statement — a
count lower bound over `letter_a` above about 120 has no witness inside the
band — is what the preregistration's two examples illustrate, and 125 and 135
are reserve rungs of the same family.

### F2. `assert_feature_words_are_specific` cannot hold unconditionally in v5

v4r4's witness constructor chose every feature word for orthogonality, so no
breaking word carried a second registered feature. v5's eight marker words are
**registered by §7.6** and their letters are what English makes them:
`whereas` contains an `a` and ends in `s`, `indeed` has a doubled letter and
is vowel-initial, `overall` has both, `though` is t-initial, `namely` contains
an `a` and ends in `y`.

None of that is a design defect and none can be designed away without changing
the marker vocabulary. What matters is whether a collision can occur **in a
cell**, and it cannot: every colliding numerator belongs to a Tier-3 family,
§7.4 admits Tier 3 to the broad-class slot alone, and §13.10 places a
broad-class companion beside B only. The check therefore asks
`assert_pair_realisable` rather than assuming, and records every tolerated
collateral feature with the reason it cannot bite.

### F3. `joint_witness` had to be generalised before v5's pool could pass

v4r4's constructor satisfied only the **first** exact-count constraint of a
pair and built an exact *sentence* count as loose terminators followed by
filler — which §9.2's rule counts as one sentence too many. Neither mattered
in v4r4, whose library held one exact-count reference family and no
sentence-exact family. In v5 both are ordinary: a realisable pair can carry
two exact counts (a marker family and a near-form family from different
feature groups), and `XC3` is an exact sentence count.

With both generalised the suite discharges **20,332 realisable pairs with zero
joint-satisfiability and zero non-entailment failures**. This is a latent
defect in carried code that v5's library exercises, found by running the
carried suite over the new population rather than by reading it — which is
what §29 of the implementation prompt asks characterization to do.

### F4. v4r4's `stages/library.py` is not carried

It is keyed on v4r4's `role` field (`reference` / `class_control`), which v5
replaces with the structural tier, and everything it did — §12.2's retention,
§12.6's coverage criterion and expansion, §12.7's budget — is in
`stages/regime.py` under v5's rules. Carrying a stale role-keyed module would
be exactly the unexecuted downstream path with a latent contract defect that
this repository has already been bitten by.

---

## 5. Defects found by executing the lifecycle

Section 4 records what reading the documents found. This section records what
**running** them found: eleven defects that only appear when a stage executes,
in code that would have produced or read v5's numbers. None changes an existing
result — there are no v5 results — and each would have changed a future one.

Every entry is an **implementation defect** unless it says otherwise. The
protocol text is right in all eleven; the code did not do what it says.

### D1. §9.1's absent verdicts were written with no slot

`run/execute.generate_and_score` built its `slot` lookup from the cell's
*stated* constituents, so every verdict on an instrument the prompt did not
state was written `slot: null`.

Two things depend on that slot. κ(R|B) — §13.6's entire input, and the reason
v5 scores every registered instance on every row — is indexed by slot, so it
was unreadable through `ObservationTable`. And §25's load-0 cell states
nothing, so by §9.1 **every** verdict on it is absent: all of them became one
key per block and the chance rates collapsed.

The slot now comes from the replication's slot map, which is the binding that
defines what a slot is. An instance the map does not bind falls back to its own
label, so no score is ever written without one.
`tests_v5/test_row_indexing.py` pins both halves.

### D2. `ObservationTable` tested presence before the arm

A load-0 verdict is an absent verdict by §9.1 *and* a chance observation by
§25. The two are different quantities read off different cells and the **arm**
is what separates them; testing `present` first routed every chance
observation into the κ index, where they collided. The difficulty coordinate is
`(p_solo − κ)/(1 − κ)`, so nothing that reads chance could have been formed
from real rows. The arm is now tested first.

### D3. A composed cell's companion was the next label in the score list

With §9.1 scoring every registered instrument on every row, that list holds one
entry per instrument — so `next(s for s in slots if s != slot)` named an
unstated instrument as the companion and collapsed distinct composed cells onto
one index key. The companion is now the cell's other **stated** constituent.

### D4. `delta_difficulty` was registered and never computed

It is a member of F1 (§15), §11.7 defines its estimator, §17.2 defines its
refit-per-replicate bootstrap, and `bootstrap_family` already accepted a
callable member for exactly this case. Nothing built the `SpectrumInput` or
called it.

Two consequences, and the second is the one that matters: the quantity was
absent from the analysis, and **F1's studentised maximum-modulus critical value
was taken over five members instead of six**, so every F1 interval was narrower
than §15 registers. `run/analysis_run.spectrum_inputs` now builds §11.7's nine
points per configuration from the freeze's slot map, and the member is
registered as the callable §17.2 requires.

### D5. §20 names `Delta_R` as masked-phase non-computable and the code computed it

`MASKED_PHASE_FORBIDDEN_MEMBERS` listed `delta_difficulty` and the fit's
coefficients but not `Delta_R`, though §20's text names both: A's point is
inside the permuted group, so a contrast of A against the reference set is a
contrast against a set A may have been permuted into. The masked record
therefore carried an estimate of the study's primary quantity formed against
permuted companions — the one number the mask exists to withhold. Added, and
the withheld members are now recorded on the masked record by name.

### D6. `assert_delta_difficulty_not_masked` read a key no record carries

It scanned `result["families"]`; an estimate record's shape is
`configurations` / `cross_configuration`. The guard ran over an empty dict on
every masked run and could not fail — a check on the execution path that was
not checking anything. It now reads the record's own shape, including the
interval families, and it is what keeps D5 fixed.

### D7. §20's masked-view cleanliness rule was never applied

`assert_masked_view_clean` existed and no caller invoked it. It is now on the
path that writes the masked view, over the records it is about to write.

### D8. `MASKED_VIEW_EXCLUDED_FIELDS` excluded `arm` — *corrected, with the argument*

This one is a **narrowing of a v5 implementation constant**, not a defect in
carried code, and it is recorded here because it is the only entry that
relaxes anything.

The masked analysis cannot build an observation table without separating §25's
load-0 cell from a solo cell from a composed one, and `arm` is the field that
says which. Excluding it made the masked stage unrunnable. It is also not
companion-identifying: the permutation moves labels *within* an (outcome,
configuration, block) group, and every composed member of such a group carries
the same `arm`, so the field is constant across everything the mask could have
swapped and narrows the true companion not at all. The integration test asserts
that property over the **written artifact** rather than leaving it in prose.

`cell_id` and the true `companion_slot` remain excluded; the cell's identity
travels as a pseudonym hashed under the sealed mask key, so §9.1's absent
verdicts stay indexable without their constituents appearing anywhere.

### D9. §31's result table emitted six of its twenty-one fields

`_intervals` computed the standard error and the marginal bounds and discarded
them; `_report_rows` filled six fields; `assert_row_traceable` refused the
table, which is the check working. Every §31 field is now filled from a signed
record — the difficulty coordinate and the reference-pool tier from the freeze,
the bounds and the standard error from the bootstrap, the cell counts from the
confirmatory record, the variance decomposition from the freeze's
`variance_reestimate` with its source named, and the achieved detectable effect
as §16.3's reading of the realised simultaneous half-width, with that
derivation travelling on the row rather than being asserted.

`iota_a` and `solo_compliance_a` were declared in `run/contracts.py` as read by
Gate 5 and were not read; they are now bound into the freeze.

### D10. §33 check 8 read a declaration of absence as the thing it forbids

The check scans a Gate-4 record for a field naming an outcome-driven selection.
Gate 4 carried `no_substitution_after_failure` — §13.14's refusal, in prose —
and the scan flagged it.

Renaming the key would have left the check as weak as it was, so the check was
**strengthened** instead: declarations of absence live in one
`declared_refusals` block that the scan skips and that the check now
*requires*. A record that simply omitted the refusal used to pass; it now
fails.

### D11. §33 check 15 had no producer and reported `UNRESOLVED` forever

It scans the v5 artifact texts and every caller passed `None`, so it returned
`UNRESOLVED` at every stage that ran it — a check that never ran.
`reuse_ledger.collect_artifact_texts` now supplies them from a declaration the
check itself owns, and refuses a named artifact that is absent rather than
silently scanning nothing. Check 15 is therefore discharged at
`PREFREEZE_AUDIT`, as §33 states.

Only **check 14** is deferred, because it reads the final-report table and no
table exists at stage 12. `run/final_report_checks.py` discharges it at
`FINAL_REPORT` — over the numbers the audit record itself says were deferred,
not over this module's constant — beside twelve traceability checks that only
become checkable once the table exists.

---

## 6. Two rules that were unsatisfiable rather than hard

### R1. `can_freeze` could not be reached however the study went

`run_prefreeze_audit` required an empty `UNRESOLVED_REDTEAM_FINDINGS`, which is
a static register that never empties, and §33 checks 14 and 15, which read
artifacts that do not exist before the freeze. A gate that cannot pass is not a
strict gate; it is a broken one, and the failure mode is that it gets waived.

A finding now blocks while **its registered mitigation is still an open
decision**, and its mitigation is a §34 decision. **R5 has none**: §13.8's
realised-drift qualifier closes its second half and its first half — κ(R|B) is
measured under B, so the reference set is a function of how each model writes
under its own B at its own m\*, and Δ_R on two models is two differently
constructed counterfactuals — is not closeable by a rule at all. It is recorded
as a **permanent limitation** and reported separately from the blockers, so it
cannot be quietly discharged by closing something.

### R2. `producing_commit_clean` was waived in the synthetic namespace

The rule is right: a run whose declared producing commit does not contain the
code that produced it has no provenance. But a developer's worktree is dirty by
construction, so the harness waived it — making provenance the one rule the
integration test never exercised.

The waiver is gone from production code entirely. The harness builds an
**isolated repository** instead (`synthetic_lifecycle.synthetic_repo`): the v5
source tree, the two documents §18 stage 1 binds by hash, the §30 ledger's
sources, the lockfile and the v5 artifact texts, copied and committed, in about
0.05 s. The production checks then run unmodified against a tree that genuinely
satisfies them — `clean_worktree`, `commit_hashable`, `tracked_implementation`,
`producing_commit_clean` and `protocol_hashes_agree`, none of them waived.

---

## 7. What the first four researcher closures changed, and what they exposed

Recorded here rather than in §1–§3 because none of these is a *discrepancy*:
each is a researcher decision arriving and the implementation catching up.
Where the closure exposed something the implementation had wrong, that is
flagged as `IMPLEMENTATION_DEFECT` and fixed under §33's rules.

### D18 — the strong L3c requires the near-form arm

`STALE_DOCUMENTATION`, retroactively. §17.6 said an L3c emitted without the arm
carries a fixed sentence; the code did that; and both were written before the
decision existed. The closure makes the two conclusions **different claims**
rather than one claim with a qualifier: `l3c_scope` is `strong` or
`same_form_only`, the sentences differ, and `L3C_STRONG_CONCLUSION_WITHHELD` is
a new registered identification status.

**The `precondition` branch's meaning changed, and this is the one place a
reader could be misled.** The pre-closure implementation read "precondition" as
*withhold L3c entirely*. That is stricter than what the researcher chose. The
researcher's words are explicit — a same-form pool "may only justify the
narrower conclusion" — so the narrow conclusion is emitted and the strong one
is unreachable. The withheld-entirely branch no longer exists in the source; it
was never reachable, since D18 was open for the whole of its lifetime, and no
record anywhere carries a statement produced by it.

**Dead code removed.** `emit_l3` maintained a `withheld` list for L3c
statements it never emitted. With every branch of `l3c_disposition` now
emitting, the list was unreachable, so it is gone and
`claims.assert_l3c_scope` is called on the built statement instead — which is
the stronger check, because it also constrains a renderer that never consulted
the emitter.

### D16 — the complete population, and what that made load-bearing

`IMPLEMENTATION_DEFECT` in the reuse rule, exposed rather than caused by the
closure. `_reusable_rows` compared `(row_id, prompt_hash, scientific_seed)`.
That is enough to catch a changed topic or a changed seed, and **not** enough
to catch a changed completion cap, a changed model revision, a changed decoding
policy or a changed protocol identity — each of which changes what the model
writes and none of which is in a prompt hash. Under the standing proposal the
volume was small enough that the gap was theoretical; the complete-population
rule makes candidate calibration 86,016 generations per replication, and at
that volume a wrong reuse is both likely and expensive.

The key is now the row's complete scientific identity, and it is **two** keys,
because generation and scoring have different inputs:

* `generation_identity` — study, protocol identity, stage, decoding projection,
  model revision, topic, **split**, block, cell, constituents, wording indices,
  prompt hash, draw, seed. A stored generation may satisfy a planned row only
  when every one of these agrees.
* `observation_identity` — the above, plus the verifier hash and §9.1's
  instance set. Written on every scored row.

Splitting them is not an optimisation. Rows are rescored from their text on
every pass, so a verifier change moves every *verdict* and regenerates nothing;
merging the keys either way would cost a full regeneration for a verifier fix,
or let a stale verdict survive one.

**The split is in the key explicitly.** §6.2 makes the two calibration sets
disjoint, so their prompts differ and a hash over the prompt would in practice
never collide. "In practice never" is not the guarantee §13.7 needs, and
`test_the_split_is_in_the_key_explicitly_and_not_by_luck` holds the topic, the
prompt and the seed fixed and moves only the split.

### D6 — irreversible, and the block that was five members wide

`IMPLEMENTATION_DEFECT`. `analysis_run._licensed` blocked five members under
`REFERENCE_SUPPORT_NOT_IDENTIFIED`: `Delta_R`, `Delta_1..3` and
`delta_difficulty`. The registered families carry **48** reference-dependent
members. The other 43 were attempted, returned no vector because the admitted
design supplies no cell for them, and were recorded `not_computable` — which
reads as *the design was never asked* rather than as *§34 D6's verdict*, and
which the freeze and the final report could not be checked against.

The set is now derived by one rule in `protocol/identification.py` — a member is
reference-dependent when its name names a core reference, a spectrum rung or the
reference mean, or when it is one of the aggregates computed from them — and the
partition is asserted against `FAMILY_MEMBERS` by a test, so a family added
later cannot fall between the two halves. 48 affected, 22 not; the 22 include
$D(B{\leftarrow}A)$, $D(A{\leftarrow}B)$, $\Lambda$, $\Delta_{\text{near}}$ and
$\Delta_{\text{broad}}$, which is exactly the set the closure exists to keep.

One subtlety the rule had to get right: F6's contrasts are written
`vac(B|B+R1)-vac(B solo)`, where the `|` is a conditional bar, and F5's are
written `Delta_R|vacuity_forced`, where it separates a member from its variant.
Splitting on `|` for both classified every F6 contrast against a reference as
reference-free.

### D3 — the bank, and the check that scanned nothing

`IMPLEMENTATION_DEFECT`. §6.2's fourth authoring rule — no wording that itself
mentions a letter, a word length, a punctuation count or a capitalisation
requirement — is the one rule a machine can check, and
`topics.assert_authoring_rules` read `question["text"]`. The schema field is
`question`. It had been scanning the empty string for every topic in the bank
since the function was written, so the only mechanically enforceable authoring
rule had never rejected anything.

Fixed to read `question`, with `text` still accepted so a differently-shaped
row is not silently exempted, and a row with no question text at all is now an
offence rather than a pass.

**A second thing the authored bank exposed.** The first draft of the 96
collided with the wider bank in three questions verbatim and about a dozen
semantically — against **composed** and **confirmatory** topics, not against
Calibration-A. §6.2's disjointness is over all six sets, and a Calibration-B
question that repeats a confirmatory topic's text spends a reserved topic's
content. `assert_sets_disjoint` caught the three verbatim collisions at load — the check
working, on the first bank it had ever been given — and the semantic ones were
found by a content-overlap scan and rewritten.
`test_the_authored_bank_is_disjoint_from_every_other_set` now runs both the
calibration-pair check and the all-sets one, because the first would have
passed all three verbatim collisions: none of them was against Calibration-A.

### D1 — the blocked call that did not exist

`IMPLEMENTATION_DEFECT`. `decisions.py` named
`design.cells.admitted_arms_from_decision` in D1's `blocks_calls`, and no such
function existed. `decisions_blocking_call` would have answered for a name
nobody could call, and the *design-time* arm set — what the study registered it
would attempt, as distinct from what a replication's Gate-3 verdicts admit —
had no producer at all. It exists now, with `d1_scale` beside it, because a
budget is arms × models × blocks × draws and naming only the arms leaves three
of the four factors to whoever writes the runner.


---

## 8. What adoption changed, and the one estimator defect it exposed

The remaining fifteen §34 closures, U2 and P1, taken on 2026-08-23. Same rule
as §7: none of these is a *discrepancy*, and where a closure exposed something
the implementation had wrong it is flagged `IMPLEMENTATION_DEFECT`.

### D17 — the construct floor, and the denominator it is measured on

`IMPLEMENTATION_DEFECT`, and the most consequential thing in this section.

The closure is $\kappa^{B}(m^{*}) \le 0.50$ on the point estimate, and the
threshold was derived — in `d17_b_strength_decision.md` — from a curve
recomputed on v4r4's **load-zero** calibration answers. Gate 2's registered
`chance` rate is not that quantity. `cell_rates(present=False)` collects every
row where the instance was absent, and in Gate 2's focal grid that includes the
$B$-solo cells at the other seven severities: answers written under a stated
length budget, which satisfy a *looser* budget far more often than an
unconstrained answer does. Applying the threshold to that rate would have been
a threshold calibrated on one estimator and applied to another under the same
name — the exact failure §33 asks the reconciliation to catch.

**Fixed, without moving anything else.** `cell_rates` gained an `arm` filter
and `instance_rates` an optional `unconstrained_arm`; Gate 2 computes both and
records both, and only the floor reads the load-zero one. The registered
`chance` rate keeps the denominator it was defined with, because §13.6's
$\kappa(R \mid B)$ is *deliberately* measured under $B$ — that is R5's whole
subject — and changing it would have altered what every reference admission
means.

**The synthetic fixture had encoded the defect's invisibility.** Its
$\kappa^{B}$ curve was flat at 0.67 across every severity, because `_compose`
conflated "B stated and scripted to fail" with "B not stated" — both produced
the same answer shape. A floor cannot be exercised against a curve with no
shape. The fixture now draws an unconstrained answer's longest word from a
length distribution shaped after the measured development curve and scripts a
$B$-failing row as one word past *its own* stated budget, so B's scripted solo
rates are unchanged and $\kappa^{B}$ runs 0.000 to 0.823 across the grid.
These are fixture numbers; nothing reads them as evidence.

### D17 — where the threshold lives

`STALE_DOCUMENTATION`, pre-emptively avoided. The obvious implementation of a
closed D17 is a constant in `construct_strength.py`, and that is exactly the
move §34 exists to stop: the code needs a number, the number gets chosen by
whoever writes the line, and the choice is never recorded as one. The quantity,
value, semantics and derivation are the `spec` field of the D17 closure in the
record; `registered_floor()` reads them; the module carries no number; and
`signing_blockers()` reports `FLOOR_NOT_SPECIFIED` if a `floor` closure ever
arrives without them. `decisions.recorded_spec` is the general mechanism, for
any decision whose *value* has no room for its own parameters.

### U2 — a resolution that is a fact about the record, not a default

See §2's U2 entry, now marked RESOLVED. The one thing worth repeating here:
adopting A2 by writing `formulation="A2"` into the signature would have looked
identical and been wrong, because the refusal would have been replaced by a
default. `adopted_formulation()` reads the open-item registry instead, so the
fit still refuses if the resolution goes away, and
`test_the_fit_still_refuses_if_u2_is_reopened` is what keeps that true.

### U2 and P1 — resolutions had no durable home

`IMPLEMENTATION_DEFECT`. `decisions.py` had a committed record; `open_items.py`
had only `resolve()`, which lives for the length of a process. U2 **blocks the
registration manifest outright**, so a resolution that vanished on exit was a
researcher act nothing preserved. `open_items` now reads an `open_items`
section of the same record file, applies it at import, refuses a record that
disagrees with a live resolution as a §32 amendment, and
`reopen_all_for_testing` restores the recorded state rather than a blank one —
the same shape as `decisions`. `record_hash` covers both sections, because a
hash over half the file would let U2's resolution change under a signature that
did not move.

### P1 — a confirmation nothing enforced

`IMPLEMENTATION_DEFECT`, minor. `CONFIRM_AT_ADOPTION` items are not blocking by
design — nothing executable turns on them — but `signing_blockers()` therefore
did not notice that P1 had never been confirmed, and signing without it would
have been signing a document nobody read. `UNCONFIRMED_AT_ADOPTION` is a new
blocker kind covering exactly that gap.

### D1 — a budget the manifest could not reproduce

`IMPLEMENTATION_DEFECT`. The generation budget was derived in
`tools/v5_compute_budget.py`, and the registration manifest binds the adopted
option. A manifest cannot import a tool, so the number would have had to be
copied — and a figure a signature carries that the code cannot reproduce is a
figure nobody can check. The derivation moved to `dci1v5.design.budget`; the
tool is now the regenerable report over it, and
`test_it_binds_the_design_d1_actually_registered` asserts the manifest's figure
*is* `budget.registered_budget()`.

### D4 — an approval that bound nothing

`IMPLEMENTATION_DEFECT`. `assert_marker_vocabulary_approved` returned the eight
words, and the manifest bound a word list. Neither made a post-adoption
substitution *detectable*: swapping `though` for `albeit` would have changed no
bound value. `marker_population()` now binds the eight families with their
statistic ids, discourse roles, rules, ladders and reserves under a
`population_hash`, and the four accepted limitations travel with it — because
"approved" must not be readable as "no concern was found", and D4's audit
referred three markers to the researcher precisely on concerns that were
accepted rather than answered.

### The rest — eleven closures that exposed nothing

D0, D2, D5, D7–D15 each closed at the document's own standing proposal, and
each already had both branches constructed behind `decisions.choice`. Nothing
in the implementation changed for any of them. Two carry a recorded red-team
objection that the closure does **not** answer — R13 against D7's 0.90 and R2
against D15's transfer — and in both cases the objection is bound into the
manifest beside the value rather than resolved by it.
