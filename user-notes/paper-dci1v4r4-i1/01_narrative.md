# 01 — Bullet-point narrative

> **Two studies, two roles (added 2026-08-24).** This narrative is v4r4's, and
> every quantity in it is v4r4's. Its successor **v5 has since been executed
> and closed**: it was a prospectively registered attempt to repair the
> companion-specific identification failure described here, and **no
> replication reached confirmatory generation**, so it adds *no* estimate to
> anything below. v4r4 supplies the behavioural composition result; v5 supplies
> a prospectively tested identification failure. Neither study identifies a
> companion-specific effect, and v5's outcome is **not** a null result and
> **not** corroboration of v4r4's effect. See
> `04_v5_prospective_followup.md`.

Iteration i1, step 1 of the compress-then-expand process
(`guidelines-narrative-and-process.md`). Commit `3d57ad2`. Evidence bundle
`paper/v4r4_bundle/`.

**Source shorthand** used throughout this folder. Full paths, field paths and
record hashes are in `EVIDENCE_MAP.md`.

| tag | artifact |
|---|---|
| `UA:<model>` | `paper/v4r4_bundle/tier0_results/<model>/UNMASKED_ANALYSIS.signed_record.json` |
| `MA:<model>` | `paper/v4r4_bundle/tier0_results/<model>/MASKED_ANALYSIS.signed_record.json` |
| `G2:<model>` `G3:<model>` `G4:<model>` `G5:<model>` | `paper/v4r4_bundle/tier1_protocol_and_gates/<model>/GATE_*.signed_record.json` |
| `TERM:<model>` | `paper/v4r4_bundle/tier1_protocol_and_gates/<model>/terminal_report.json` |
| `FR` | `paper/v4r4_bundle/tier0_results/final_results.json` |
| `COV` | `paper/v4r4_bundle/tier1_protocol_and_gates/reports/coverage.json` |
| `CP47` | `paper/v4r4_bundle/tier1_protocol_and_gates/reports/cp4_cp7_analysis.json` |
| `G1D` | `paper/v4r4_bundle/tier1_protocol_and_gates/reports/gate1_decision.json` |
| `ADM` | `dci1/reports/dci1v4r4/followup_diagnostics/02_admission_landscape.json` (post-hoc diagnostic; verdicts computed by the registered `stages.selection` functions on the signed Gate-2 table, per its own `_provenance` field) |

---

## What the candidate claim set got wrong

Three corrections, made before the claims are fixed rather than after.

**C1's "at fixed instruction count" is false and must be struck.** `D(c←g)` is
solo compliance minus composed compliance — `dci1v4r4.analysis.observations`
forms one cell mean per constituent per cell, and the contrast subtracts the
one-instruction cell from the two-instruction cell. Instruction count is not
held fixed; it moves from one to two. The estimand that *does* hold count fixed
by swapping the companion is `Delta_R`, and `Delta_R` is `NOT_IDENTIFIED`
study-wide [`FR` → `study_level_not_identified`]. Writing "at fixed instruction
count" would claim precisely the thing the study failed to identify. The
registered statement text carries no such phrase: it reads *"composing the two
instructions costs D(A<-B) a delivery loss whose simultaneous interval lies
wholly above zero"* [`UA:qwen3-4b` → `payload.claims.outcome_first.statements[1].statement`].

**C2's "three distinct routes across three models" is two routes.** Measured:
`gemma-3n-e4b-it` admitted one budget family (`RF9`) which could not straddle
ι_A; `qwen3-4b-instruct-2507` admitted one budget family (`RF7`) which could not
straddle ι_A — the same shape. `qwen3-4b` admitted two families (`CR5`, `RF11`),
both of which straddle and both of which supply a valid triple, and fell one
short of the registered three [`ADM` → `models.<model>.families`,
`n_core_references`; `G3:<model>` → `core_references`, `dropped_for_no_triple`].
The v5 development report reaches the same reading and calls the two Gemma-and-
Qwen-instruct cases "same shape"
[`dci1/reports/dci1v5/reference_design_development.md` §5.1].

**C2's "local sparsity immediately above ι_A" is right but understates what was
measured.** The candidate rung population is *asymmetric* around ι_A on all
four checkpoint runs. That asymmetry is a **post-hoc diagnostic** of the
shortlisted pool, not a registered outcome and not shown to be a binding cause;
counts below in C2.

**The same asymmetry recurred prospectively in v5, under a registered
criterion.** v5 measured 14–21 eligible rungs above ι_A against 143–163 below
on every replication, and three of four then failed the registered support
criterion (§12.6 C4: 4, 5 and 5 qualifying straddling feature groups against a
required 6), recording irreversible D6 non-identification. This does **not**
convert v4r4's diagnostic into a demonstrated cause — no ablation exists — but
it does mean the same structural shape was observed again under a bar fixed
before data. `04_v5_prospective_followup.md`.

A second review pass then demoted C3 out of the claim set entirely and split
C1 by position. The paper carries **two** claims. See `ITERATION.md`.

---

## C1 — Composition costs delivery, and the two position-matched cells are the clean ones

**Calibrated strength: narrow**, and stated as **four separately licensed
statements**, not one study-level conjunction. §17's simultaneous intervals
control error *within a declared multiplicity family in one configuration of one
checkpoint run*. No registered procedure controls error across the four-cell
conjunction "at least one detectable loss in every configuration of both
survivors", so the paper does not assert that conjunction as a single 95%
guarantee. It reports four statements and lets the reader count them.

**Claim, as it may be written — split by position, because the design splits.**
§11.4 is explicit that a solo cell states its constraint in position one, so
`D(c←g)` is position-matched to its baseline **only** where *c* is stated first,
and in the other configuration it confounds added load with a change of
position.

- **Position-matched (2 of 4 cells).** Where the outcome constraint is stated
  first, `D` isolates a solo-to-composed difference with no position movement.
  Both such cells emit L1 for `D(A←B)`: +0.1159, simultaneous [+0.0771, +0.1546]
  on `gemma-3n-e4b-it`, and +0.3919, simultaneous [+0.3503, +0.4335] on
  `qwen3-4b`.
- **Position-shifted (2 of 4 cells).** Where the outcome constraint is stated
  second, composition and position change together and the quantity is not
  attributable to composition alone. Both such cells emit L1 — `D(B←A)` = +0.2832
  [+0.2485, +0.3179] on `gemma-3n-e4b-it`, `D(A←B)` = +0.3291 [+0.2835, +0.3747]
  on `qwen3-4b` — and both carry `POSITION_CONFOUNDED` [`UA:<model>` →
  `payload.claims.outcome_second.position_status`].

The identity of the constraint showing a detectable loss varies across the four
cells. No registered contrast tests that variation, and §11.4 names the
position-clean quantities that would have carried it — `Delta_R` and
`delta_difficulty` — both of which are `NOT_IDENTIFIED`.

**Motivation.** A practitioner who composes two verifiable instructions needs to
know whether both are delivered. In both position-matched cells, at least one
instruction shows a detectable reduction in verifier-defined compliance. That is
an aggregate rate difference over blocks, not a finding that any instruction is
categorically undelivered in a given response.

**Evidence.**

- Twenty interval-bearing estimates, two checkpoint runs × two configurations ×
  five quantities — **twelve are delivery-loss quantities** (`D(B<-A)`,
  `D(A<-B)`, `D(B<-CL)`) and **eight are derived contrasts** (`Lambda` =
  `D(B<-A)` − `D(A<-B)`, `Delta_class` = `D(B<-A)` − `D(B<-CL)`). Each carries a
  simultaneous 95% interval, a marginal interval and a bootstrap standard error
  [`UA:<model>` → `payload.result.<configuration>.families.<F>.members.<member>`].
  Full table in `EVIDENCE_MAP.md`.
- The L1 emissions, four in total, two position-matched and two
  position-shifted [`UA:<model>` →
  `payload.claims.<configuration>.statements[*].emitted`, `.position_status`].
- The largest **focal** losses are the four `D(A←B)` and `D(B←A)` values above.
  `D(B←CL)` reaches +0.7946 on `gemma-3n-e4b-it` and is larger than any of them;
  it is a class-companion quantity, not a focal one, and is reported separately.
- Precision: T = 384 blocks, M = 8 draws, 24,576 rows per checkpoint run, 49,152 in
  total, complete with zero missing, duplicated or unexpected rows
  [`.../CONFIRMATORY_GENERATION.signed_record.json` → `payload.completeness`].
  Realised half-widths 0.0244 to 0.0577; every registered precision precondition
  met.
- Block bootstrap, 10,000 resamples, studentised maximum-modulus simultaneous
  intervals within declared multiplicity families [`UA:<model>` →
  `payload.resamples`, `payload.result.<cfg>.families.<F>.critical_value`].

**What the reader should be able to do afterwards.** Quote the two
position-matched losses as composition effects, quote the two position-shifted
ones only with the registered caveat, and see that the study registers no test
of the variation between them.

**Boundary carried with C1.** No cross-configuration and no cross-model estimand
is registered, and the records store no bootstrap replicates, so neither
difference can be formed after the fact. L2 — directional asymmetry — is
withheld in all four configurations, because its gate requires L1 in both
directions and no configuration achieves that.

---

## C2 — The companion counterfactual was not identified, and the attrition is measured

**Calibrated strength: existence-proof.** What follows separates three things
the first draft ran together: the **registered gate outcomes** that defeated
identification, the **post-hoc diagnostics** that describe why the candidate pool
became small, and a **scope restriction** that was never a cause at all. Only the
first is a signed finding.

**Claim, as it may be written.** The contrast this design exists to form — the
same instruction count with the companion replaced by a difficulty-matched
reference — was not carried through to confirmatory estimation on any
checkpoint run. The gate outcomes that produced that are on signed records. The
decomposition of *why the candidate pool was too small* is a post-hoc diagnostic
computed with the registered selection functions on the signed Gate-2 tables, and
it is labelled as such.

**What actually defeated identification — the registered gate outcomes, signed.**

1. **Fewer than three admitted core references on three of four checkpoints.**
   §13.4 requires three. Admitted: `gemma-3n-e2b-it` 3, `qwen3-4b` 2,
   `gemma-3n-e4b-it` 0, `qwen3-4b-instruct-2507` 0 [`G3:<model>` →
   `core_references`].
2. **No spectrum triples on two checkpoints**, recorded as
   `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` [`G3:<model>` →
   `identification_statuses`, `dropped_for_no_triple`].
3. **The reduced design composes no reference cell**, so F2, F4 and F7 exist in
   no configuration of either survivor [`UA:<model>` →
   `payload.result.<cfg>.families`].
4. **Gate 4 ended the one full design.** `gemma-3n-e2b-it` assembled the 47-cell
   design and was terminated at `COMPOSED_HEADROOM_FAILURE` before generating a
   confirmatory row [`TERM:gemma-3n-e2b-it`].

**A note on the second Gate-4 failure, which is not a cause here.**
`qwen3-4b-instruct-2507` also terminated at Gate 4, on `solo:CL` at 0.9896 — a
class-companion *solo* ceiling already determined at Gate 2 [`TERM:qwen3-4b-instruct-2507`
→ `failures`]. That checkpoint had **zero** admitted core references before Gate
4 ran [`G3:qwen3-4b-instruct-2507` → `core_references`], so its companion
counterfactual was already unidentified. The Gate-4 failure is an observed
outcome, not an additional cause of non-identification, and the paper says so.

**Diagnostics of reference attrition — post-hoc, and not shown to be binding.**

These describe the shape of the candidate pool. **No ablation or sensitivity
analysis in this study shows that relaxing any one of them would have made
`Delta_R` identifiable**, and the paper does not claim it would.

- **The candidate ladder is skewed harder than *A*.** Unconditionally, **65 of
  the 84 rungs Gate 2 calibrated lie below ι_A**, and eligible rungs strictly
  above ι_A number **2, 1, 1 and 0** across the four checkpoint runs. *What the
  84 are:* the severity rungs of the six budget-class families §12.3 shortlisted
  on each checkpoint run — 21, 20, 23 and 20 — pooled across the four. They are
  not 84 distinct constraints and they are not the measured library: the
  pre-screen measured 254 eligible rungs per checkpoint run, of which 67, 69, 73
  and 46 were eligible as reference rungs across 17–18 families, and §12.3
  carries six families forward [`COV` → `eligible_rungs_measured`,
  `support.eligible_reference_rungs`]. The shortlist rule reserves a slot below
  and a slot above ι_A per family wherever the pre-screen has one
  [`dci1v4r4.stages.regime.shortlist`], so the skew is measured on a set built to
  reach above *A*, not on a set selected for being below it. *The caveat that
  travels with the count:* the shortlist was chosen on pre-screen ι and the
  landscape reports Gate-2 calibration ι, and on the same 84 rungs the pre-screen
  split is 54 below / 30 above ι_A against 65 / 19 at calibration. **Seventeen
  rungs changed side — 14 above→below and 3 below→above** (51 stayed below, 16
  stayed above); the 65/19 split is that net movement of 11, not 14 one-way
  crossings. So part of the skew is a pre-screen-to-calibration shift rather than
  a fixed property of the library [`ADM` → `...rungs[*].prescreen_iota`;
  derivation in `EVIDENCE_MAP.md` Table 3 rows 2d–2g]. Conditioning on
  refusal — a narrower statistic, since the denominator is already the refused
  set — 58 of the 66 rungs refused for a caliper miss lie below ι_A. On the two
  checkpoints that admitted a single family, that family's only admissible rung
  was the **top of its measured ladder** (`RF9:13` at ι = 0.7043 against
  ι_A = 0.6948; `RF7:24` at ι = 0.5920 against ι_A = 0.5963), so no spectrum rung
  existed above it. [`ADM`]
- **Closeness is not equivalence.** Of the 18 rungs inside the 0.10 caliper,
  **9 were refused: 8 because the Newcombe interval does not intersect ±0.05, and
  one — `RF11:26` on `gemma-3n-e4b-it` — on the pre-screen caliper alone.** The
  Newcombe refusals are a property of the calibration sample, 96 solo topics at
  `M_CAL` = 4, not of the library. [`ADM`]

**A scope restriction, not a cause — the structural-class decision.** §13.7
refuses every production-class family from the core pool *before measurement*
[`ADM` → `refused_before_measurement`], and *A* is production-class. **The
registered design therefore never intended `Delta_R` to hold structural class
fixed.** `Delta_R` is the excess of *A* over budget-class companions matched on
ι, and `COMPANION_CLASS_NOT_MATCHED` is the permanent statement of that
[`G3:<model>` → `identification_statuses`; class sentence in
`SCOPE_STATEMENTS.md` §5].

This resolves an ambiguity the first draft carried on both sides. **In `A+B`
versus `R+B`, companion identity and structural class move together**, so the
introduction may not say "only the companion's identity moves". Class exclusion
is a **domain restriction on what `Delta_R` would have meant**, not one of the
causes that defeated it, and it is reported in the scope paragraph rather than in
the attrition list.

**The consequence, named.** `Delta_R`, `Delta_j`, `Xi`, `delta_difficulty`,
`D(B<-R_j)` and `D(R_j<-B)` have no interval anywhere in the study [`FR` →
`study_level_not_identified`], with the registered sentence that they are *"not
null results, not zero, and not missing by accident"*.

**What the reader should be able to do afterwards.** Distinguish the registered
gate outcomes from the post-hoc attrition diagnostics, run the two
pre-composition diagnostics against their own candidate library, and see that the
class restriction is a scope condition rather than a failure.

**Boundary carried with C2.** The preregistered procedure did not carry a
validated companion contrast through to confirmatory estimation. **It does not
follow that the library could support no executable design**: `gemma-3n-e2b-it`
assembled the full 47-cell design, and `qwen3-4b` reached two admitted core
references against a registered requirement of three. Whether a different
caliper, a different equivalence rule or a different admission order would have
produced a usable pool is untested here.

---

## Provenance — reported, not claimed *(was C3)*

**Not a claim.** Demoted on review from the third claim to methods and
limitations reporting: Gate 1 and the freeze go to §2, the L4 episode and the
§31 objection to §6.1, and §6 is cut. The material is unchanged; what changed is
that the paper no longer asserts it. Three reasons. A claim about one's own
protocol invites the reading that the paper is marking its own homework. The
nine-page limit is binding and §4 is the section under pressure. And the claim
sits awkwardly beside an unresolved §31 objection about whether v4r4 should have
been adopted at all — a paper cannot assert that its device bound while carrying
a live objection that the device was bent.

**What the material reports.** The gate-and-freeze machinery is not decoration
around the estimates: the gate outcomes determined which designs ran, the
recorded lifecycle order runs freeze → generation → masked analysis → unmasking,
and when a defect was found in the claim emitter after unmasking the protocol
refused to let the researcher repair it. The invalidated field is reported beside
the registered reading rather than corrected. **The ordering is what the records
state, not what the signatures prove** — HMAC under a key the researcher holds
establishes integrity only against parties without that key, and cannot
establish that a record existed before unmasking. See `SCOPE_STATEMENTS.md` §6.

**Motivation.** *Conditional, and stated that way.* **How common demonstrated —
as opposed to asserted — preregistration is in this literature is a question
pending CITE-07** (`GAPS.md`); §3.5 leaves it open and this paragraph may not
close it. What is observable without any citation is local: in this study the
device is inspectable in the artifacts, including in the one place where it cost
the author something. Whether that is unusual is not asserted.

**Evidence.**

- **Gate 1 at scale.** Ten registered deterministic conditions over a final
  instrument population of 524 [`G1D` → `measurement_rule.conditions`,
  `instrument_population`]: three-process determinism at agreement 1.0 over 400
  responses [`G1D` → `determinism`]; an independent reimplementation from prose
  alone at agreement 1.0 over 36,164 responses and 650,952 statistic
  comparisons with zero failures [`G1D` → `reimplementation`]; 92,148 witness
  pairs with no joint-satisfiability or non-entailment failure [`G1D` →
  `witnesses`]; a frozen boundary suite of 164 cases and 1,280 checks [`G1D` →
  `suites`]; mutation validation passed [`G1D` → `mutation_validation.passed`].
- **One sealed analysis.** Both surviving checkpoint runs were analysed under a single
  analysis code hash `dffb5a86…9ca`, identical in the masked and the unmasked
  record, with `identical_computation_as_masked: true` and agreeing
  `masked_artifact_hash` [`MA:<model>`, `UA:<model>` → `analysis_code_hash`,
  `masked_artifact_hash`, `identical_computation_as_masked`]. The hash establishes that
  one computation produced both sets of numbers. It does **not** establish
  scientific comparability: the two checkpoint runs ran at different operating
  points (n\*/m\* = 4/10 and 2/12) and against different class companions
  (`CL7:80` and `CX1:4`), and the paper does not pool them. The phrase "what
  makes the two replications comparable" appears in the repository's own
  summaries; it overstates what a code hash can do and is not carried forward.
- **The defect the device would not let its author fix.** `emit_l4` compares
  the *set* of levels any member reached rather than the level each named member
  reached, and `run/analysis_run.py` hands it input with member identity already
  discarded. On `gemma-3n-e4b-it` both configurations reach L1, so the sets
  match and L4 is emitted, while every named member's classification flips
  [`paper/v4r4_bundle/tier0_results/EXECUTION_REPORT.md` §8.3]. The emitted
  statement reads *"the same classification holds in every registered
  configuration: ['L1']"* [`UA:gemma-3n-e4b-it` → `payload.claims.L4.statement`];
  the registered reading beside it records
  `licensed_by_the_registered_rule: false`,
  `members_replicating: []` and
  `members_differing_across_configurations: ["F1:D(A<-B)", "F1:D(B<-A)"]`
  [`FR` → `analysed.gemma-3n-e4b-it.l4_registered_reading`]. It was not
  repaired because `run_unmasked_analysis` refuses an unmasked analysis under
  code differing from the masked seal and §20 forbids regenerating a mask once
  semantic identities are known [`EXECUTION_REPORT.md` §8.3].
- **The mask's limits, stated rather than implied.** On the reduced design *A*
  and `CL` each carry exactly one companion, so four (outcome, configuration)
  groups are structurally unmaskable and the masked record says so
  [`MA:<model>` → `mask_effectiveness.structurally_unmaskable`,
  `.structurally_unmaskable_note`]. `D(A<-B)` — the only L1 that recurs across
  both configurations on `qwen3-4b` — is among them.

**What the reader should be able to do afterwards.** Distinguish a
preregistration that constrains from one that narrates, by asking for the
artifact in which the device cost the author something.

**Boundary carried with this material.** The device did not prevent the defect; it
prevented the repair. And the §31 objection is live in the protocol's own text:
v4r3 §31 forbids an amendment that weakens a criterion to make a gate pass, and
v4r4 was adopted after §10.4-R2 failed — *"A reader is entitled to hold that
§31 forbids it and that halting was the registered answer; that reading is
recorded here as a live objection and is not argued away"*
[`user-notes/DCI1_preregistration_v4r4.md` lines 163–167]. The paper carries the
objection; it does not resolve it.

---

## Novelty delta

Every item here is **`TODO(CITE)`**. The repository contains no `.bib` file and
no prior Related Work draft (verified: `find . -name '*.bib'` returns nothing
outside `.venv` and `.git`), so no positioning statement below has been checked
against a primary source. See `GAPS.md` §Related Work.

- **Possibly new — stated as a hypothesis about prior work until CITE-02 is
  checked.** A measured account of reference attrition in a
  constraint-composition design: the registered gate outcomes plus the two
  pre-composition diagnostics, with counts. `TODO(CITE)` — whether any prior
  benchmark reports admission-level attrition of its controls. **Nothing in the
  paper may assert that prior work assumes reference-pool existence until this
  is verified.**
- **Possibly new — CITE-03.** A directional, solo-anchored, both-orders
  delivery-loss estimand at load two with preregistered gates, masking and
  within-family simultaneous intervals. `TODO(CITE)` — whether prior work
  reports a *directional* per-constraint loss rather than a symmetric co-failure
  statistic. **Whether v4r4 stands alone depends on CITE-02 and CITE-03
  together**, not on CITE-02 alone: if C2's account is known but C1's estimand is
  not, the paper still has a contribution, and the reverse also holds.
- **Extends prior work, subject to verification.** Whether composing
  instructions degrades compliance is already established in the
  instruction-following literature is **a question pending citation, not a
  premise** — the repository has checked no source for it, and writing "not in
  dispute" would concede priority that has not been verified. If it is
  established, what C1 adds is the estimand and its precision — a directional,
  solo-anchored loss with registered simultaneous intervals — **not** the
  discovery. Provenance is not part of that: the bundle and the signed records
  are reported for auditability in Appendix G and are not a scientific
  contribution of C1. `TODO(CITE)` — CITE-01, CITE-03.
- **Inherited.** The block bootstrap with studentised maximum-modulus
  simultaneous intervals; Šidák multiplicity control; Newcombe intervals for the
  equivalence rule; the construct-validity framing of benchmark measurement.
  `TODO(CITE)` for each.
- **Not claimed as novel.** Order sensitivity in multi-constraint prompts.
  `TODO(CITE)` — the repository's own audit notes prior work reporting position
  effects, and this paper's contribution there is at most the load-two,
  per-member registered classification.

---

## Claim boundary — what the paper does not claim, and why the design cannot license it

| Not claimed | Why the design cannot license it |
|---|---|
| That *A* interferes with *B* specifically, or more than a matched companion would | `Delta_R`, `Delta_j`, `Xi`, `delta_difficulty`, `D(B<-R_j)`, `D(R_j<-B)` are `NOT_IDENTIFIED` study-wide [`FR`]; L3a–L3e are unreachable in every configuration |
| That the loss is directionally asymmetric | L2 is withheld in all four configurations; its gate requires L1 in both directions and no configuration achieves that [`UA:<model>`] |
| That the result replicates across configurations **as a study-wide finding** | L4 is not licensed on `gemma-3n-e4b-it` [`FR` → `l4_registered_reading.licensed_by_the_registered_rule` = false]; §28.1 *Configuration dependence* is the registered reading there. On `qwen3-4b` the registered rule **does** license L4, for the single member `F1:D(A<-B)` [same field, `= true`, `members_replicating`]. One checkpoint run's L4 is not a study-wide replication claim, and the paper makes none |
| That companion identity does not matter | Non-identification is not a null [`FR` → `not_identified_note`] |
| Anything about compliance as an independent human would judge it | The measurement basis is `deterministic_measurement_validated` and never `human_validated`; §10.5's scope sentence attaches permanently [`G1D` → `measurement_basis`, `scope_sentence_is_permanent`] |
| That the model or position effect is tested | No cross-model and no cross-configuration estimand is registered in v4r4, and the records store no bootstrap replicates |
| Generalisation beyond two checkpoints, one constraint pair, load two, one topic space, one decoding policy | Two of four checkpoint runs produced no confirmatory row; terminal statuses carry no evidence about the effect [`TERM:<model>` → `terminal_sentence`] |
| That one artifact certifies the whole provenance chain | `lifecycle_integrity.json` covers records through Gate 4 only; Gate 5 onward verify individually [see `SCOPE_STATEMENTS.md` §4] |
| That the signatures establish *when* a record was written, or by whom | The records are HMAC-SHA256 under a symmetric key held by the researcher. HMAC establishes integrity relative to that key; it does not establish authorship or temporal precedence, because a key-holder can generate a valid HMAC at any time. See `SCOPE_STATEMENTS.md` §6 |
| That the library cannot support an executable replacement design | `gemma-3n-e2b-it` assembled the full 47-cell design; `qwen3-4b` reached two of three core references. What failed is the preregistered procedure, not the library's capacity |
| That relaxing any single admission diagnostic would have identified `Delta_R` | No ablation or sensitivity analysis was run. The diagnostics describe the pool; they are not shown to be binding causes |
| That `Delta_R` would have held structural class fixed | §13.7 refuses production-class families from the core pool by construction, so companion identity and structural class move together. `COMPANION_CLASS_NOT_MATCHED` is permanent |
