# 03 — Full-paper outline

Step 3 of the process. Structure per `guidelines-bullet-point-outline.md`;
section-level conventions per the matching guideline for each section. Source
shorthand in `01_narrative.md`. NeurIPS main body is nine pages; the page budget
below is a plan, not a promise.

**Working title.** **Deferred.** See `TITLES.md`: no title is finalised until
the literature search establishes what the reusable contribution is.

**Terminology, fixed here.** The four model checkpoints are **checkpoint runs**.
They share one candidate-library construction, so they are not independent
replications of the library phenomenon; the paper says "four checkpoint runs"
and reserves **replication** for L4's registered cross-configuration sense.

**Claim tags.** C1 composition cost · C2 non-identification and its measured
attrition. **Two claims.** Provenance and the commitment device (formerly C3) are
reported in §2.7 and §6.1 and are not claimed.

**Related Work placement.** *After the Introduction.* The paper may be
correcting a methodological assumption that lives in prior work — **that is a
hypothesis pending CITE-02, not an established positioning** — and if it holds
the reader needs the map before the gates. Two-tier: §3 carries the argumentation on a tight citation set;
Appendix F carries coverage by field-level question.

---

## §1 Introduction — 1.25 p · serves C1, C2

Carried forward verbatim from `02_intro_outline.md`. Ends on the **two-item**
contributions list.

*Reader can afterwards:* name the two claims, separate the registered gate
outcomes from the post-hoc attrition diagnostics, and say what the paper does
not claim.

---

## §2 Problem setting and estimands — 1.0 p · serves C1, C2

Per `guidelines-background.md`: setup, notation, standard methods, nothing novel.

- **2.1 The compliance vector.** One prompt, one response, one deterministic
  verdict per instruction present. Define `X_c ∈ {0,1}`.
- **2.2 The block.** One topic with its wording assignment; every cell of a
  block shares them. T = 384 blocks, M = 8 draws per cell
  [`UA:<model>` → `payload.blocks`, `payload.result` grain; grain independently
  visible in `paper/v4r4_bundle/tier2_data/per_block_cell_means.csv`].
- **2.3 Delivery loss.** `D(c←g)` = solo − composed, per block, averaged over
  blocks. **State plainly that it contains the generic cost of a second
  instruction.** This paragraph is where C1's boundary is set.
- **2.4 The companion contrast.** `Delta_R`, `Delta_j`, `Xi`,
  `delta_difficulty`, and what each isolates. Define them here even though none
  is identified — the reader cannot follow §4 otherwise.
- **2.5 The difficulty coordinate.** ι = instructed compliance, chance-corrected;
  the 0.10 calibration caliper and the 0.15 pre-screen caliper
  [`dci1/src/dci1v4r4/protocol/constants.py:233,235`].
- **2.6 The claim ladder.** L1 through L4, their licensing rules, and the
  identification statuses that withhold them. **Name the two grains here**, since
  Table 2 is built on them: L1–L3 are emitted per member within a configuration;
  L4 is one cross-configuration classification per checkpoint run. Table 2 slot.
- **2.7 How the study was run and sealed.** One short paragraph, receiving what
  the cut §6 carried: the gate sequence as executed, Gate 1's measurement basis,
  the freeze at commit `450a049`, and the mask. Reported so the reader can read
  §4 and §5; **not** advanced as a contribution. Detail → Appendix B and G.
- **Appendix pointer:** full estimand algebra → Appendix A.

*Reader can afterwards:* read every number in §5 without re-reading §2, and see
why `D` and `Delta_R` are different questions.

---

## §3 Related work — 0.75 p · serves C2 (novelty), C1 (positioning)

Per `guidelines-related-works.md`. **Every citation in this section is
`TODO(CITE)`** until checked against a primary source; the register is
Appendix E.

- **3.1 Constraint-composition benchmarks.** What they measure, and the
  hypothesised delta: that none forms a companion-replacement contrast, so none
  separates identity from count. **Written as a question until CITE-02 is
  checked**, not as an assertion about the field.
- **3.2 Pairwise interaction statistics.** What this study measures is not in
  question: `D(c←g)` is directional and solo-anchored, and on `qwen3-4b`
  `D(A←B)` and `D(B←A)` have opposite signs, which a symmetric statistic could
  not represent. **Whether prior interaction statistics are in fact symmetric
  co-failure or correlation measures is written as a question until CITE-03 is
  checked**, not as an assertion about the field. `TODO(CITE)`.
- **3.3 Position and ordering effects.** This paper claims no novelty here and
  reports its own configuration dependence as a scope condition, not a finding.
  **That disclaimer rests on CITE-04 and is stated conditionally until it is
  checked** — a wrong citation here would overclaim in the other direction, by
  conceding priority that may not exist. `TODO(CITE)`.
- **3.4 Construct validity in benchmark measurement.** The framing this paper
  inherits, and the specific requirement it operationalises: that additional
  subtasks must not confound the measurement. `TODO(CITE)`.
- **3.5 Preregistration in ML.** **Whether the practice is sparse in this
  literature is a question pending CITE-07**, not a premise. What this paper adds
  if it is — a worked case with signed artifacts — is reported in Appendix G and
  is not claimed as a contribution either way. `TODO(CITE)`.
- **Appendix pointer:** coverage by field-level question → Appendix F.

*Reader can afterwards:* locate the paper on the map and state the one thing it
does that the cited work does not.

---

## §4 The identification attempt and where it failed — 2.25 p · serves C2 · **the paper's centre**

Per `guidelines-methods.md` for the design half and `guidelines-results.md` for
the outcome half; organised **per claim**, so setup and evidence sit adjacent.

- **4.0 What this section does.** Opening sentence names C2 and the three-way
  split the section is organised on: the **registered gate outcomes** that
  defeated identification (signed), the **post-hoc attrition diagnostics** that
  describe why the pool was small (not shown to be binding), and the
  **structural-class scope restriction**, which was never a cause.
- **4.1 The registered design.** Five arms, the 47-cell full block and the
  8-cell reduced block of §8.6, both orders within block, four checkpoints.
  What varies, what is fixed, the pre-specified analysis plan.
  [`G3:<model>` → `design_variant`, `cells_per_block`, `variant_rule`]
- **4.2 The gate sequence.** Gate 1 measurement → Gate 2 operating point →
  Gate 3 reference admission → Gate 4 composed headroom → Gate 5 freeze. One
  sentence each on what may and may not be read at each. Emphasise
  `reads_no_composed_cell: true` on Gates 2 and 3 [`G2:<model>`, `G3:<model>`].
- **4.3 The scope restriction — structural class, decided by the protocol.**
  §13.7 refuses production-class families from the core pool before measurement;
  *A* is production-class. **`Delta_R` was therefore never intended to hold class
  fixed**: in `A+B` vs `R+B`, companion identity and structural class move
  together, and `COMPANION_CLASS_NOT_MATCHED` is the permanent statement of it.
  This is a domain restriction on what `Delta_R` would have meant, **not** a
  cause of its non-identification, and the section says so before the diagnostics
  begin. [`ADM` → `refused_before_measurement`; `G3:<model>` →
  `identification_statuses`]
- **4.4 Diagnostic 1 — the ladder is skewed harder than *A*.** Of the 84 rungs
  Gate 2 calibrated across the four checkpoint runs — the severity rungs of the
  six budget-class families §12.3 shortlisted on each, 21/20/23/20 — **65 lie
  below ι_A**; eligible rungs strictly above ι_A number 2, 1, 1, 0. Say in one
  clause what the 84 are, so the count is not read as the measured library:
  §12.3's shortlist reserves a slot below and a slot above ι_A per family where
  the pre-screen has one, and the pre-screen measured 254 eligible rungs per
  checkpoint run. **Second qualifier, stated with the first:** the shortlist was
  chosen on pre-screen ι and re-measured at Gate-2 calibration ι, where the same
  84 split 54/30 before and 65/19 after — 14 moving above→below, 3 below→above,
  17 changing side — so part of the skew is that shift rather than a fixed
  property of the library. Lead with the unconditional counts and report the
  58-of-66 refusal split as a secondary diagnostic, labelled conditional. On the
  two single-family checkpoints the admitted rung was the top of its family's
  ladder, so no spectrum rung existed above it. Both counts are **descriptive**;
  neither is shown to be what bound the design. **Figure 2 slot.**
  [`ADM`; `COV` → `eligible_rungs_measured`; `EVIDENCE_MAP.md` Table 3 rows 2d–2g]
- **4.5 Diagnostic 2 — closeness is not equivalence.** Of 18 in-caliper rungs, 9
  refused: **8 by the Newcombe region and one on the pre-screen caliper alone**
  (`RF11:26` on `gemma-3n-e4b-it`). The Newcombe refusals are a calibration-sample
  property at 96 topics × `M_CAL` = 4. [`ADM` → `thresholds.N_SOLO`, `.M_CAL`,
  `.REFERENCE_NEWCOMBE_REGION`]
- **4.6 What Gate 3 admitted.** Two routes to the reduced design, one route to
  the full design. **Table 3 slot.** [`ADM`, `G3:<model>`]
- **4.7 The composed-headroom validation, which needs composed cells and is
  therefore not a pre-composition diagnostic.** `gemma-3n-e2b-it`: five failing
  cell-slots, all involving `RF11` composed with *B*, 0.9583–1.0000 against
  [0.05, 0.95]; `RF11:26` was 0.6875 solo. `qwen3-4b-instruct-2507`: one
  failure, on the class companion's *solo* cell at 0.9896 — not a composed
  effect. **Figure 3 slot.** [`TERM:<model>`, `G2:gemma-3n-e2b-it`]
- **4.8 Gate 4 revised nothing, by rule.** No reference replaced, no caliper
  widened, no rung re-chosen; a headroom failure is terminal for the
  checkpoint run. This paragraph pre-empts the "why not just pick a different
  reference" objection. [`G4:<model>` → `computes_no_contrast`, `ranks_nothing`;
  `TERM:<model>` → `terminal_sentence`]
- **4.9 The margin was thin and the record said so before the outcome.** C4's
  leave-one-family-out sweep; three of four checkpoint runs have no margin.
  [`COV`, `CP47` → `leave_one_family_out_finding`]
- **4.10 What is therefore not identified.** Six estimands named; F2, F3, F4,
  F7, F8 absent from every configuration; the registered `not_identified_note`
  quoted verbatim. [`FR`, `UA:<model>`]
- **Closer (draft).** "The replacement design is not merely unexecuted here; it
  did not carry a validated companion contrast through to confirmatory
  estimation. One checkpoint run assembled the full design and one reached two of
  three core references, so the library is not shown to be incapable of
  supporting an executable design — what failed is this procedure on it."

*Reader can afterwards:* compute both attrition diagnostics against their own
candidate library from solo cells alone, know that composed-headroom validation
is only available after composition, and keep the two kinds of evidence apart —
**both attrition diagnostics are post-hoc descriptions** computed from
`02_admission_landscape.json`, while the signed, registered evidence is the
separate set of gate outcomes in §4.6–§4.8.

---

- **4.x (candidate, new) The prospective follow-up.** *Added 2026-08-24 after
  v5 was executed; placement not yet decided — this subsection or a parallel
  one in §6.* §4's account of why identification failed is **retrospective**.
  v5 registered a design to repair it, froze it, ran it, and **still did not
  carry a matched-companion comparison into confirmatory analysis**: 459,312
  rows, zero replications reaching confirmatory generation. Three failed the
  registered support criterion (C4 realised 4, 5, 5 against 6) with
  irreversible D6 non-identification; the sole identified replication then
  terminated at the independent composed-headroom gate. The contribution is
  that the two bottlenecks are **sequential and separable**, which v4r4's
  entangled retrospective account could not show. Carries **no** effect
  estimate and **no** null: `NOT_IDENTIFIED` is a failure to identify, not a
  finding of no effect. Full treatment and the caveat separating v5's fitted
  *design* from its prospective *execution*:
  `04_v5_prospective_followup.md`. Whether this earns its own subsection, and
  whether it belongs in §4 or §6, is undecided and gated on the literature
  review.

## §5 What the surviving design licenses — 1.5 p · serves C1

- **5.0** Opening sentence names C1 and its narrow strength.
- **5.1 The two survivors.** 8-cell design, 24,576 rows each, complete;
  operating points n\*/m\* = 4/10 and 2/12 [`G2:<model>` → `n_star`, `m_star`;
  `CONFIRMATORY_GENERATION.signed_record.json` → `payload.completeness`].
- **5.2 Uncertainty protocol.** Block bootstrap, 10,000 resamples, studentised
  maximum-modulus simultaneous intervals within F1/F5/F6/F9; precision
  preconditions and realised half-widths.
- **5.3 The twenty estimates.** **Table 1 slot.** Both interval types and the
  bootstrap SE for every one.
- **5.4 What L1 licenses, per member, per configuration.** Emitted statements
  quoted in their registered wording, each carrying its position caveat.
- **5.5 What is withheld and why.** L2 in all four configurations; L3 entirely;
  L4 on `gemma-3n-e4b-it`. Reasons quoted from the records. **Table 2 slot.**
- **5.6 Robustness that is already in the record, not added.** F5's
  vacuity-forced and graded-0.99 recodings, and F6's vacuity gate — these are
  registered families, not post-hoc checks, and they are labelled as
  pre-specified. [`UA:<model>` → `payload.result.<cfg>.families.F5`, `.F6`]
- **Closer (draft).** "Composition costs delivery; nothing here says the cost
  is about *B* in particular."

*Reader can afterwards:* quote any of the twenty numbers with its interval and
its scope sentence, and say which claim level it does and does not license.

---

## §6 Discussion — 1.75 p · serves both claims

> **Renumbered.** The former §6 (the commitment device) was cut when C3 was
> demoted; Discussion moves up from §7 to §6 and Conclusion from §8 to §7.
> Sub-numbers below are written as §6.x and every cross-reference in this folder
> uses the new numbers.

**Redistribution of the cut section, as applied.** Gate 1 as executed and the
freeze/mask/unmask machinery are now §2.7, with detail in Appendices B and G.
The mask's structural limits, the invalidated L4 field with its registered
reading, and the live §31 objection are items (viii), (ix) and (v) of §6.1
Limitations below. Table 4 moves to Appendix B. The freed 0.75 p goes to §4.
**No §6.x sub-section duplicates that material**; the sub-numbers below are the
only ones in force.

Per `guidelines-discussion.md`, limitations first.

- **6.1 Limitations.** (i) Everything estimated here rests on **two of the four
  checkpoint runs** — one constraint pair, load two, one topic space, one
  decoding policy; the other two produced no confirmatory row, and a terminal
  status carries no evidence about the effect.
  (ii) The measurement basis is verifier-defined, never human-validated —
  §10.5's scope sentence, quoted. (iii) `COMPANION_CLASS_NOT_MATCHED` describes
  the design. (iv) Cross-model and cross-configuration differences are
  described, not tested. (v) The §31 objection, quoted and not resolved.
  (vi) C4 with no leave-one-family-out margin on three of four. (vii) The
  `lifecycle_integrity.json` coverage boundary. (viii) What the mask could not
  hide: four structurally unmaskable (outcome, configuration) groups on the
  reduced design, including `D(A←B)`, stated in the masked record's own words
  [`MA:<model>` → `mask_effectiveness`]. (ix) The invalidated L4 field: the
  emitter compares the set of levels reached rather than the level each named
  member reached, so on `gemma-3n-e4b-it` L4 was emitted while every named
  member's classification flipped; the registered §28.1 reading is reported
  beside it and the two rules that forbade repair are named. On `qwen3-4b` the
  registered rule does license L4 for one member, so this is a defect in one
  checkpoint run's emitted field, not a study-wide withholding.
- **6.2 Alternative explanations, unresolved.** Three objections the study
  cannot close, each stated with what it would take to close it (`GAPS.md` G16).
  *"The references were simply badly chosen"* — the admission functions are
  registered and the refusal reasons are recorded per rung, so the choice was
  not discretionary [`ADM` → `_provenance`]; that rules out cherry-picking, and
  does **not** show the rule was a good one. *"The caliper was too tight"* — 58
  of the 66 caliper misses lie below ι_A, which is suggestive and not decisive:
  **no re-selection at a wider caliper was run**, so what a wider caliper would
  have admitted is unmeasured. *"Gate 4 was too strict"* — the failing rates are
  0.9583–1.0000 and **no minimum detectable effect was computed** for the
  [0.05, 0.95] band, so how much headroom those rates leave is unquantified.
  Written as open questions, not as answers.
- **6.3 What the design would need.** Drawn from
  `dci1/reports/dci1v5/reference_design_development.md` §§4–5, under two
  conditions stated in the text: every threshold there was chosen after
  observing all of v4r4, so it is **design fitting and is never called
  validation**; and the file is cited at its producing commit `89604f6`.
  *(Correction to the task's framing: this specific file is tracked and clean at
  `3d57ad2` — `git diff HEAD` on it is empty — so the "uncommitted source"
  caveat does not apply to it, though other files under `dci1/reports/dci1v5/`
  and `dci1/src/dci1v5/` are modified. The design-fitting condition applies in
  full.)* Two points only, and the text keeps the two sources apart. **What v4r4
  establishes:** a reference admitted on its solo rate reached 0.9688 composed
  and breached the headroom band (§4.7), and the shortlisted ladder ran harder
  than *A* on every checkpoint run (§4.4). Those are motivating problems, from
  this study's own records. **What the v5 report proposes, and v4r4 does not
  establish:** a specific pre-composition quantity, κ(R│B), and the projection
  p̂(R│B+R) built from it (§4.2–§4.3 of that report), plus a target shape for a
  candidate library (§5.1). The report **does** recompute κ on v4r4's stored
  Gate-2 B-solo responses and compare p̂ against observed Gate-4 rates — so the
  paper must not say the quantity was never computed on v4r4's cells. What it
  must say is that **v4r4 does not establish that it predicts Gate-4 failure**:
  the quantity was defined after the Gate-4 outcomes it is checked against were
  known, the comparison covers **one** checkpoint run — `gemma-3n-e2b-it`, the
  only full design that reached Gate 4 — and the admission thresholds in §4.5
  were fitted to that same evidence. It is not a registered v4r4 quantity, sits
  on no signed record, and no v4r4 gate consumed it. So the v5 material is a
  *proposal motivated by* v4r4, never a result *validated by* it, and only a
  prospective design could test it. **If a reviewer objects to any use of the v5
  material, what survives is only the two motivating problems** — v4r4's own
  §4.7 headroom breach and §4.4 ladder skew. The κ/p̂ proposal does **not**
  survive the removal: v4r4 registers no such quantity and no v4r4 record carries
  one, so it is not substitutable from this study's evidence. The text says that
  plainly rather than implying the two halves are interchangeable
  (`GAPS.md` G10, red-team R10).
- **6.4 Implications.** Benchmark builders: both attrition diagnostics read
  solo cells only and can be computed **before any composed-cell generation**,
  with the caveat that neither is shown here to be a binding cause;
  composed-headroom validation cannot — it needs the composed cells. Reporters of composition effects: direction and anchor. Preregistration
  practice: one episode in which the device prevented a repair its own author
  wanted, reported for auditability and not offered as a general argument.
- **6.5 Future work.** A prospective corrected design: a same-form, chance-free
  candidate library, screened on both attrition diagnostics before any composed
  cell, and a pre-composition interaction quantity used as an admission gate.
  What such a design could establish is bounded by the design itself — whether
  **it** admits three core references and carries a companion contrast through
  to confirmatory estimation. It could not establish that `Delta_R` is or is not
  estimable in this constraint vocabulary generally, and the paper does not say
  a single experiment would settle that.
- **6.6 Reflections and tacit knowledge.** → Appendix H.

*Reader can afterwards:* state the strongest objection to the paper and the
paper's answer to it.

---

## §7 Conclusion — 0.25 p, or cut

`guidelines-conclusion.md` prefers omission to padding, and §6 already closes
the paper. **Default: cut.** If retained, five moves in four to six sentences,
limitations-first, naming one boundary only — the absent companion
counterfactual — and one future direction.

---

## Figures and tables

Full specification in `FIGURE_PLAN.md`. Slots and takeaways:

| slot | § | claim | one-sentence takeaway |
|---|---|---|---|
| **Figure 1** | §1 | C2 | **Deferred pending the literature search.** Draft takeaway: of four preregistered checkpoint runs, reference admission and composed-headroom validation left two — both on the reduced design — which licenses twenty interval-bearing estimates and none of the six companion-specific estimands the study was built to measure. |
| Figure 2 | §4.4 | C2 | The candidate ladder is skewed harder than the target constraint on every checkpoint run: of the 84 shortlisted rungs Gate 2 calibrated, 65 lie below ι_A, and at most two eligible rungs sit above it on any one run. |
| Figure 3 | §4.7 | C2 | The admitted reference `RF11:26` measured 0.6875 solo and 0.9688 composed with the outcome constraint *B*, exceeding the registered [0.05, 0.95] headroom ceiling. |
| Table 1 | §5.3 | C1 | In the two position-matched cells a composed constraint loses delivery relative to itself alone; the two position-shifted cells confound composition with position, and the table marks which is which. |
| Table 2 | §5.5 | C1, C2 | L2 and L3 are withheld in every cell and L4 is withheld on `gemma-3n-e4b-it` but licensed on `qwen3-4b`; the record names the rule in each case. Two bands: L1–L3 per configuration, L4 once per checkpoint run — L4 is a cross-configuration classification and is not repeated per configuration. |
| Table 3 | §4.6 | C2 | Two routes to the reduced design: one admitted family that cannot straddle, or two that can and a registered requirement of three. |
| Table 4 | App. B | — | Gate 1's ten conditions were met at agreement 1.0 across 524 instruments, 36,164 responses and 650,952 statistic comparisons. Moved out of the main body with §6. |

---

## Red team — objections a skeptical reader will raise, and where each is answered

| # | objection | answer | where | weight |
|---|---|---|---|---|
| R1 | "You are reporting a failed study." | The non-identification is measured rather than inferred, its gate outcomes are signed, and the estimates that survived are separately reported and preregistered. Whether that amounts to a contribution a venue will take is unresolved pending CITE-02/CITE-03. | §1, §4.0 | load-bearing |
| R2 | "The reference pool was badly chosen." | Registered selection rules out cherry-picking; it does not show the rule was good. Open. | §6.2 | **unresolved** |
| R3 | "Widen the caliper." | 58 of the 66 current caliper misses lie below ι_A, so most of what the caliper currently excludes is on the harder side. **No wider-caliper re-selection was run**, so what widening would actually admit — and whether it would repair the asymmetry — is unknown. Open. | §6.2, Fig. 2 | **unresolved** |
| R4 | "Gate 4 was too strict." | Failing rates 0.9583–1.0000, but no minimum detectable effect is computed. Open. | §6.2 | **unresolved** |
| R5 | "n = 2 models." | Stated as the first limitation; terminal statuses carry no evidence. | §6.1 | accepted |
| R6 | "The verifier is not a human." | §10.5 scope sentence, permanent, quoted on every claim. | §6.1, `SCOPE_STATEMENTS.md` | accepted |
| R7 | "L4 says it replicates." | On `gemma-3n-e4b-it` the emitted field is invalidated and the registered §28.1 reading is *Configuration dependence*. On `qwen3-4b` the registered rule does license L4, for one member. There is no study-wide replication claim either way. | §6.1 | load-bearing |
| R8 | "v4r4 amended a protocol after a gate failed." | §31 objection quoted, not argued away. | §6.1 | accepted |
| R9 | "Why should I trust the numbers?" | Verified bundle, signature and hash checks, coverage boundary stated. | Appendix G | load-bearing |
| R10 | "The v5 material is post-hoc." | Conceded **for the v5 development report** — named as design fitting, never called validation; only the two motivating problems are supportable from v4r4's own records, and the κ/p̂ proposal does not survive if the report is removed. **Narrowed 2026-08-24:** the v5 *run* is not post-hoc — it was registered, frozen and executed without amendment, and its outcome (zero replications reaching confirmatory generation) is prospective evidence. The two must be cited separately. | §6.3, `GAPS.md` G10, `04_v5_prospective_followup.md` | accepted, narrowed |

---

## Appendix plan

Ordered to mirror the body, per `guidelines-appendix.md`. Omit any that stays
empty.

- **A. Estimand algebra and the claim ladder.** Full definitions of `D`, `Λ`,
  `Delta_R`, `Delta_j`, `Xi`, `delta_difficulty`; L1–L4 licensing rules and the
  identification statuses. Serves §2.
- **B. Protocol and execution detail.** Gate-by-gate settings; the 66 §18.1
  freeze fields and the two `reduced`-variant exemptions; decoding policy, model
  revisions, chat-template hash, environment and dependency digests; seed
  scheme. Serves §4, §6.
- **C. Additional results.** The F5 and F6 families in full; per-cell raw rates;
  the complete Gate-4 tables for all four checkpoint runs (46 cells on
  `gemma-3n-e2b-it`). Serves §5.
- **D. Qualitative samples.** Selection protocol stated in §5 before any sample
  appears. **Open: whether to include any. See `ITERATION.md` Q4.**
- **E. Citation verification register.** Every `TODO(CITE)` with the claim it
  supports, whether load-bearing, what was checked, what remains unverified.
  Serves §3.
- **F. Related-work coverage by field-level question.** The second tier.
  Serves §3.
- **G. Reproducibility and artifact statement.** The bundle: 53 present, 3
  derived, 6 missing; the verification results; the `lifecycle_integrity`
  coverage boundary; what a reader can and cannot reproduce from a clone.
  Serves all claims.
- **H. Tacit knowledge.** Replication traps: the producer-with-no-consumer
  defect class; the caliper value that appears wrongly in one internal report
  and never entered any selection; the absence of a §27 codebook.
- **Result-insertion map:** not applicable — every experiment in this paper has
  run. The map convention applies to papers whose experiments have not.

**Stand-alone test.** No claim in the abstract or introduction depends on an
appendix. §4 carries the registered gate outcomes, both attrition diagnostics
and the composed-headroom validation with counts; §5 carries the twenty
estimates. Appendices carry verification, not evidence.
