# ITERATION — paper-dci1v4r4-i1

## State

Steps 1–3 of `guidelines-narrative-and-process.md` are complete: bullet-point
narrative, introduction outline, full-paper outline, with the supporting
registers the sourcing rules require. **No prose, no LaTeX, no figures.** Per
the guideline, this is the point at which feedback is cheapest, and the process
stops here for review.

**Update, 2026-08-24 — v5 is no longer only design fitting.** When this bundle
was written, v5 existed as a *proposed* successor and its material entered the
outline solely as design fitting. v5 has since been **registered, frozen and
executed to its close**: 459,312 real rows, and **zero replications reached
confirmatory generation**. Three lost reference identification under D6 (C4
realised 4, 5 and 5 qualifying straddling feature groups against a registered
6); the one that kept identification then terminated at composed headroom. So
the bundle now spans two studies with distinct roles — v4r4 supplies the
behavioural composition result, v5 a **prospectively tested identification
failure**. See `04_v5_prospective_followup.md`.

The design-fitting caveat still applies to the v5 *development report*, whose
thresholds were chosen after observing v4r4. What changed is that the fitted
design was then registered and run without amendment, so the **execution** is
prospective even though the **design** is not. G10 and R10 are narrowed, not
withdrawn. **v5 produced no `Delta_R` and no other confirmatory estimate**, and
`NOT_IDENTIFIED` is not a null result.

## What this rests on

| | |
|---|---|
| Repository | `/home/cnm13ryan/git/dci` |
| Commit read at | `3d57ad2cd93321658f20d1afa87420205d89fc59`; re-checked at `3c14d66` — `git diff --name-only 3d57ad2..HEAD` touches **no** v4r4 artifact, no `paper/` file and no file in this folder, so every number below still stands |
| Working tree at `3c14d66` | dirty under `dci1/src/dci1v5/`, `dci1/reports/dci1v5/`, `dci1/tests_v5/` and `CHANGES_SCIENTIFIC.md`; no v4r4 artifact modified |
| Evidence bundle | `paper/v4r4_bundle/` — 53 PRESENT, 3 DERIVED, 6 MISSING, 0 OVERSIZE |
| Bundle archive | `paper/v4r4_bundle.tar.gz`, 688,939 bytes, sha256 `8d8826b61bac15778fd581f55462418c76d8407af8f75bddae65b5a36b813b68` |
| Bundle manifest | `paper/v4r4_bundle/MANIFEST.md`, sha256 `528701fc90de8b7fb30a306ae09812f02853bbe22c52114bf30e5251bae49019` |
| Verification state | V1 24/24 signed records verify · V2 one analysis code hash `dffb5a86…` across both survivors · V3 freeze `450a049`, 24,576 rows each · V4–V6 recorded in the manifest |

**One artifact outside the bundle is cited.**
`dci1/reports/dci1v4r4/followup_diagnostics/02_admission_landscape.json`, for
both attrition diagnostics of C2, the structural-class scope restriction and
Figure 2. It is a post-hoc diagnostic whose verdicts
were produced by the registered `stages.selection` functions on the signed
Gate-2 table (its own `_provenance` field), it is labelled as post-hoc wherever
it is used, and the primary outcomes it summarises are also cited from the
signed Gate-3 records. If the bundle is treated as closed, this file should be
added to it at the next revision — see Q6.

## What was produced

| file | what it fixes |
|---|---|
| `01_narrative.md` | the two claims, calibrated; the novelty delta; the claim boundary; the corrections to the candidate set; provenance demoted out of the claim set |
| `02_intro_outline.md` | paragraph-level introduction, claims named in body order, two-item contributions list |
| `03_paper_outline.md` | section-by-section outline with the claim each serves, figure and table slots, red-team table, appendix plan |
| `EVIDENCE_MAP.md` | the twenty estimates (12 delivery-loss, 8 contrasts) with both interval types, SE, path, field path and record hash; the six `NOT_IDENTIFIED` estimands with gate and measured reason; the C2 diagnostic counts; the provenance counts; a correction log |
| `FIGURE_PLAN.md` | three figures and four tables, each with takeaway, form, data path; the Type 1 font and colour-accessibility constraints; Figure 1 deferred pending the literature search |
| `SCOPE_STATEMENTS.md` | the four mandatory sentences, verbatim, with source and destination |
| `GAPS.md` | seventeen gaps (G1–G17) and the ten-entry `TODO(CITE)` register |
| `TITLES.md` | three candidates with the criteria applied; **no title chosen**, deferred pending the literature search |

## Changes to the candidate claim set, at first draft

Three corrections made before the review pass below. All three still stand.

1. **"At fixed instruction count" struck from C1.** `D(c←g)` is solo minus
   composed, so instruction count moves from one to two. The estimand that holds
   count fixed is `Delta_R`, which is `NOT_IDENTIFIED`. As worded, C1 claimed
   the study's central failure as its result.
2. **C2's "three distinct routes" is two.** `gemma-3n-e4b-it` and
   `qwen3-4b-instruct-2507` failed the same way — one admitted family that
   cannot straddle ι_A. `qwen3-4b` is the second route: two admitted, both
   straddling, one short of the registered three.
3. **C2's "local sparsity immediately above ι_A" is understated.** The measured
   fact is a directional skew of the candidate ladder — later restated on review
   with unconditional counts — and a second, independent filter: 9 of the 18
   rungs inside the caliper are refused on precision, not location. Two
   components were added to C2 that the candidate did not name: class exclusion
   before measurement, and the Newcombe equivalence rule.

C3 was reworded from "makes C1 and C2 sayable" to a testable existence-proof.
**The review pass below then demoted it out of the claim set entirely.**

## Next stage

**Step 4 — first-draft figures — is now blocked, not merely unstarted.** Figure
1 carries C2, and whether C2 is a contribution depends on the literature search.
The revised order is: **literature search → §3 → Figure 1 → title → prose.**

---

## Review pass, 2026-08-24 — what changed and why

An external review found the documents epistemically careful about provenance
but **narratively overreaching**: turning v4r4's failure into a general
methodological contribution before establishing either its generality or its
novelty. That reading is accepted. Ten points were raised; eight are accepted in
full, one is accepted with an addition, and one surfaced an error of mine that
the review inherited rather than caught.

| # | finding | disposition |
|---|---|---|
| 1 | C2's "systematic mechanism" is too strong; the four are heterogeneous in kind | **accepted.** Retagged existence-proof; reframed at the time as four bottlenecks encountered by this procedure on this library — *superseded by the second pass's three-way split.* One component — the ladder skew — is reported as *recurring* on all four checkpoints, with the note that four checkpoints sharing one library construction are not four independent observations |
| 2 | "A benchmark that matches controls on pass rate inherits every one of these failures" does not follow | **accepted.** Replaced with the narrow form: matching on marginal difficulty did not, in this study, yield an identifiable contrast; whether another benchmark inherits any bottleneck is not established |
| 3 | Direct contradiction: "four filters checkable before any composed cell" vs Filter 4 being the composed-headroom gate | **accepted, and it was the sharpest catch.** Split at the time into three admission-stage diagnostics and one composed-headroom validation. *Superseded by the second and third passes:* the filter taxonomy is gone. C2 now carries registered gate outcomes, **two** post-hoc attrition diagnostics, and a scope restriction |
| 4 | "Twenty delivery-loss estimates" is factually wrong | **accepted.** Twelve `D(c←g)` and eight derived contrasts; corrected in five files and logged in `EVIDENCE_MAP.md` |
| 5 | C1 rhetorically claims untested model and position effects | **accepted.** Claim now reads that the identity of the constraint showing a detectable loss varies across the four observed cells, with no registered contrast testing it. "No stable rule says which" removed from the motivation |
| 6 | 58/66 is conditional on refusal and is framed too strongly; the four replications are not independent | **accepted, with an addition.** The unconditional counts were available and are now the headline: **65 of 84 measured rungs lie below ι_A**, with eligible rungs above ι_A numbering 2, 1, 1, 0. The 58/66 split is demoted to a secondary diagnostic, labelled conditional. The dependence point is stated in C2's strength tag |
| 7 | The novelty claim is being fixed before the literature search | **accepted.** Step 4 is now blocked on the search; Figure 1 and the title are deferred |
| 8 | C3 should be demoted; and "that single hash is what makes the two replications comparable" is wrong | **accepted in full.** C3 is no longer a claim: Gate 1 and the freeze move to §2, the L4 episode and the §31 objection to §6.1 (§7.1 at the time; renumbered in the second pass), §6 is cut, Table 4 moves to Appendix B, and 0.75 p goes to §4. The hash sentence is replaced — it establishes computational identity, not scientific comparability, and the two replications ran at different operating points against different class companions. The phrase is inherited from the repository's own summaries and is not carried forward |
| 9 | The titles generalise beyond the evidence | **accepted.** No title chosen this iteration |
| 10 | The package is overengineered relative to the result | **accepted as a standing risk.** The C3 demotion is the concrete response; the remaining registers are audit apparatus and stay out of the paper |

### A correction the review inherited rather than caught

The first draft said that on **both** `gemma-3n-e4b-it` and
`qwen3-4b-instruct-2507` no eligible rung sits strictly above ι_A, and the
review's point 6 repeated it as the stronger evidence. **It is false for
`gemma-3n-e4b-it`:** `RF9:13` sits at ι = 0.7043 against ι_A = 0.6948 and is
both eligible and admissible. The straddle test is against the family's **core
rung**, not against ι_A, and on both checkpoints the core rung was the top of
that family's measured ladder — `RF9:13` and `RF7:24` — so no spectrum rung
existed above it. `qwen3-4b-instruct-2507` is the only checkpoint with nothing
eligible above ι_A.

The claim as first written also appears in
`dci1/reports/dci1v5/reference_design_development.md` §5.1 and was inherited from
there rather than derived from the records. Corrected in `01_narrative.md`,
`02_intro_outline.md`, `03_paper_outline.md`, `FIGURE_PLAN.md` and
`EVIDENCE_MAP.md`; the correction log is in `EVIDENCE_MAP.md`.

### The strategic question the review raises and does not answer

> **Superseded in part by the second pass — see Q8.** The paragraph below made
> the outcome turn on CITE-02 alone, treating C2's novelty as the single hinge.
> That is wrong: **CITE-02 and CITE-03 matter independently.** If C2's attrition
> account is already known but C1's directional, solo-anchored estimand is not,
> there is still a paper, and the reverse also holds. Only if *both* come back
> known does the "no contribution left" reading apply. The corrected framing is
> Q8; the paragraph is kept for the record of what the first review argued.

The review's closing point is the largest one open: **whether this is a paper
now, or a section of a later one.** ~~If the literature search shows the
identification account is novel, v4r4 stands as a diagnostic paper. If it does
not, v4r4 has no contribution left that a venue would take~~ — C1 is a narrow
empirical result on two checkpoints of one constraint pair, and C2 would become a
re-encounter of a known difficulty *only if CITE-02 comes back known*.

The alternative the review points at is to run the corrected companion library
prospectively and test whether the `Delta_R`-type quantities become identifiable.
On that path v4r4 becomes the diagnostic study that motivated the corrected
design, which is a stronger position than carrying a paper alone. That decision
should be made **after** the literature search and **before** any prose, and it
is not this iteration's to make.

## Second review pass, 2026-08-24 — what changed and why

A fresh red team found the remaining problems were no longer mainly narrative:
C1's interpretation, what C2 has established causally, the definition of the
companion counterfactual, and several factual contradictions. Sixteen points plus
a provenance question. **All accepted.** Three were verified against the records
before acting, and all three checked out — one of them was an arithmetic error I
had introduced.

| # | finding | disposition |
|---|---|---|
| 1 | C1 attributes position-confounded differences to composition | **accepted, blocking.** C1 is now split: two position-matched cells isolate composition, two position-shifted cells confound it with position. Table 1's takeaway rewritten |
| 2 | `Delta_R`'s companion "identity" is ambiguous because class moves with it | **accepted, blocking.** Decided: §13.7 admits only budget-class families to the core pool while *A* is production-class, so the registered design **never intended `Delta_R` to hold class fixed**. Class exclusion is a **scope restriction**, not a cause. "Only the companion's identity moves" is struck |
| 3 | "Bottlenecks" asserted as causes without counterfactual support | **accepted, blocking.** C2 restructured into three parts: registered gate outcomes (signed, causal), post-hoc attrition diagnostics (descriptive, not shown binding), and the scope restriction. The `qwen3-4b-instruct-2507` Gate-4 failure is now explicitly *not* a cause of that checkpoint's non-identification — it had zero core references before Gate 4 ran |
| 4 | The Newcombe count is arithmetically inconsistent: 4+1+3+0 = 8, not 9 | **accepted, blocking, and recomputed.** Of 18 in-caliper rungs, 9 were refused — **8 by Newcombe and one, `RF11:26` on `gemma-3n-e4b-it`, on the pre-screen caliper alone**. The refusal count was right; attributing all nine to Newcombe was wrong |
| 5 | C2 overstates provenance: "recorded in the signed gate records rather than inferred" | **accepted, blocking.** Gate outcomes are signed; the aggregate decompositions are post-hoc from `02_admission_landscape.json`. Stated once in `EVIDENCE_MAP.md` Table 3 and carried in C2 |
| 6 | "Unexecutable on this library" is too strong | **accepted, blocking.** `gemma-3n-e2b-it` assembled the full 47-cell design and `qwen3-4b` reached two of three references. The claim is now that the **procedure** did not carry a contrast through to confirmatory estimation |
| 7 | Table 2 contradicts the registered L4 result on `qwen3-4b` | **accepted.** Verified: `licensed_by_the_registered_rule: true`, `members_replicating: ["F1:D(A<-B)"]`. One registered L4 survives. "Every level above L1 is withheld" is false and is removed |
| 8 | "Differs by model and by position" survived in the Table 1 takeaway | **accepted.** Cross-document regression, fixed |
| 9 | The four-cell conjunction has no multiplicity justification | **accepted.** C1 is now four separately licensed statements; the paper asserts no study-level 95% conjunction |
| 10 | The three alternative-explanation rebuttals do not establish what they claim | **accepted.** Reframed as three **unresolved sensitivities**, with the missing analysis named in each case. Red-team rows R2–R4 re-marked unresolved. New gap G16 |
| 11 | Novelty deferred in one place, presupposed in others; and standing depends on CITE-02 **and** CITE-03 | **accepted.** "Corrects a methodological assumption" and "usually assumed" are now written as questions pending the search. The CITE-02-and-CITE-03 dependence is recorded in the novelty delta |
| 12 | Provenance still appears as contribution 3 | **accepted.** Contributions drop to **two**. The bundle is an artifact and reproducibility statement in Appendix G — and "full provenance record" was wrong anyway, with six missing items and one diagnostic outside the bundle |
| 13 | The scope sentence is assigned to the wrong paragraph and may be missing from C2 | **accepted.** Reassigned to the first statement of *either* claim, and stated to apply to C2, whose ι values and admission verdicts are equally verifier-derived |
| 14 | Stale numbering after §6 was cut | **accepted.** Discussion is now §6 and Conclusion §7; all `§7.x` references renumbered; the "four-item contributions list" pointer corrected |
| 15 | "Replication" carries two incompatible meanings | **accepted.** The four models are **checkpoint runs**; **replication** is reserved for L4's registered cross-configuration sense. Fixed in the outline's terminology block |
| 16 | "Largest losses", "one decisive experiment", "all three claims survive" | **accepted.** Now "largest *focal* losses" (`D(B←CL)` = +0.7946 is larger than any of them); future work no longer claims a single experiment could settle estimability "at all in this vocabulary"; the stale sentence is replaced |

### The provenance question, verified

The reviewer asked what the HMAC signatures establish. Checked at `3d57ad2`:

- The key is **gitignored and untracked** (`git ls-files dci1/evidence/dci1v4r4/keys/`
  returns nothing), 64 bytes, mode 0600 — so it is *not* distributed with the
  repository, which was the reviewer's stated worry. The substantive point stands
  regardless: HMAC under a symmetric key held by the researcher proves integrity
  relative to that key, not authorship and not temporal precedence.
- **The freeze commit `450a049` is on no remote ref**, and `HEAD` is 114 commits
  ahead of `origin/main`. **There is no external immutable anchor for the v4r4
  chain.**

So the temporal ordering rests on local git history plus a locally-held symmetric
key. `SCOPE_STATEMENTS.md` §6 now states exactly that, `GAPS.md` G15 records the
cheap remedy — push the freeze commit, or publish a timestamped digest — and the
claim boundary forbids writing that the signatures prove the analysis was fixed in
advance. This independently supports the C3 demotion: a commitment-device claim
would have rested on an anchor that does not exist.

### What the paper is now

**Two claims.** C1, narrow, four separately licensed statements split by
position. C2, existence-proof, restructured into signed gate outcomes plus
descriptive attrition diagnostics plus a scope restriction. Provenance is an
appendix statement.

## Third pass, 2026-08-24 — reconciliation to the accepted framing

No new review. This pass propagated the second pass's framing into the places
that had not received it, and answered one factual question the framing exposed.
Nothing here changes an estimate, an interval, a gate outcome or an evidential
status.

| # | what was stale | disposition |
|---|---|---|
| 1 | `02_intro_outline.md` claimed a control "could not be built on this library", counted "three admission diagnostics plus one validation", sourced all counts to signed gate records, and said composition costs a constraint in every configuration | **all four removed.** Contribution 1 is now the registered gate outcomes plus two post-hoc diagnostics, labelled post-hoc; contribution 2 is split by position. ¶3's "four bottlenecks" and ¶5's "three admission-stage diagnostics" go with them |
| 2 | `03_paper_outline.md` carried a **duplicate §6.1–§6.5** left over from the cut commitment-device section, colliding with Discussion's own §6.1–§6.6, plus two sub-sections both numbered "Diagnostic 2" | **duplicate block deleted.** Its content is where the redistribution note promised: Gate 1 and freeze/mask to a new **§2.7**, the mask's limits and the L4 episode to §6.1 items (viii) and (ix). §4.4 is Diagnostic 1, §4.5 Diagnostic 2 |
| 3 | §6.2 read as three rebuttals | **now three unresolved sensitivities**, each naming the analysis that would close it. Matches `GAPS.md` G16 and red-team rows R2–R4, which already said unresolved |
| 4 | §6.5 future work claimed one experiment could settle whether `Delta_R` is estimable "at all in this vocabulary" | **replaced.** A prospective corrected design can establish only what **that** design admits and carries through; the general estimability question is explicitly not settleable by one experiment. The second pass logged this fix but it had not been applied to the file |
| 5 | L4 wording | `qwen3-4b` has **one** licensed L4 result (`members_replicating: ["F1:D(A<-B)"]`, re-verified). Red-team R7 and the claim-boundary row now say so; `SCOPE_STATEMENTS.md` §3's trailing "the paper makes no replication claim" is deleted as contradicting its own preceding sentence |
| 6 | "replication" used for model executions | **"checkpoint run" throughout** — narrative, intro, outline, evidence map, figure plan, scope statements. `FIGURE_PLAN.md` now has zero uses. Reserved for L4's registered sense, and for `bootstrap replicates` |
| 7 | provenance language | HMAC establishes integrity **only against parties without the key**. And the anchor remedy is directional: publishing now makes the current state checkable from that moment, and **cannot retroactively establish pre-unmask existence**. `SCOPE_STATEMENTS.md` §6, `GAPS.md` G15 and `01_narrative.md`'s provenance section all say this; the provenance section's "Claim, as it may be written" heading is gone, because provenance is not a claim |
| 8 | the `65/84` diagnostic was unexplained | **resolved from the records** — see below |
| 9 | stale terminology elsewhere | `GAPS.md` G13's "Filters 1–3", `EVIDENCE_MAP.md` Table 3's "filter" column header, `ITERATION.md`'s `§7.x` references and two stale counts, `TITLES.md`'s T2 note |

### What the 84 rungs are, resolved from the records

The count had been quoted as "84 measured rungs", which invites reading it as the
constraint library. It is not. The 84 are the severity rungs of the **six
budget-class families §12.3 shortlisted** on each checkpoint run — 21, 20, 23 and
20 — pooled over four runs, so the same family recurs across runs at a
run-specific ι. Above them sits a much larger population: the pre-screen measured
**254 eligible rungs per checkpoint run** from a **28-family** population, of
which 67 / 69 / 73 / 46 were eligible as reference rungs across 17–18 families
[`COV`].

Two things follow, and both are now mandatory wherever 65/84 appears. The
shortlist is **not** selected for being below *A* — §12.3 reserves a slot at
ι_A − 0.20 **and** one at ι_A + 0.20 per family wherever the pre-screen has one
[`dci1v4r4.stages.regime.shortlist`] — so the skew is measured on a set built to
reach above *A*. But the shortlist was chosen on **pre-screen** ι and the
landscape reports **calibration** ι, and on the same 84 rungs the pre-screen
split is **54 below / 30 above** ι_A against **65 / 19** at calibration. The
movement behind that: **51 stayed below, 16 stayed above, 14 moved above→below
and 3 moved below→above — 17 changed side**, netting the 11 that turns 54 into
65. Part of the measured skew is that pre-screen-to-calibration shift rather than
a fixed property of the library. `EVIDENCE_MAP.md` Table 3 rows 2d–2g carry
the derivation and `FIGURE_PLAN.md` makes all three points binding constraints on
Figure 2.

**This is a caveat, not a correction.** 65 of 84 remains what the records say.

## Fourth pass, 2026-08-24 — reconciliation, second round

Nine issues raised against the third pass. All accepted; one was an arithmetic
error of mine and the rest were residual wording the third pass did not reach.
No estimate, interval, gate outcome or evidential status changes.

| # | issue | disposition |
|---|---|---|
| 1 | the 84-rung transition was written as "14 rungs crossed" | **accepted — my error.** 14 is the one-way count. Recomputed: 14 above→below, 3 below→above, **17 changed side**, 51 stayed below, 16 stayed above, summing to 84 and netting the 11 that turns 54/30 into 65/19. Corrected in six files and logged in `EVIDENCE_MAP.md` |
| 2 | §4's closing implied one attrition diagnostic was signed | **accepted.** Both are post-hoc from `02_admission_landscape.json`; the signed evidence is the separate registered gate outcomes in §4.6–§4.8, and the closing now says exactly that |
| 3 | "the binding scarcity" for the eligible-above-ι_A count | **accepted.** Causal wording with no counterfactual behind it. Now descriptive in `EVIDENCE_MAP.md` row 2b, §4.4 and Figure 2's emphasis note |
| 4 | the 65/84 caveat was carried unevenly | **accepted.** Both qualifiers — shortlist not library, and pre-screen ι re-measured at calibration ι — now appear together in the introduction, §4.4, the narrative and Figure 2 |
| 5 | §6.3 blurred v4r4's own evidence with the v5 report's proposal | **accepted, and it caught a second error on the way.** Split explicitly: v4r4 establishes the headroom breach and the ladder skew as *motivating problems*; κ(R│B) and the p̂ projection are *proposals* the v5 report makes. My first draft of the fix said the quantity "was never computed on v4r4's cells" — **checked against the report and false**: §4.2–§4.3 recompute κ on v4r4's stored Gate-2 B-solo responses and compare p̂ against observed Gate-4 rates. The correct statement is that v4r4 does not *establish* prediction — the quantity was defined after the outcomes it is checked against, the comparison covers one checkpoint run (`gemma-3n-e2b-it`, the only full design to reach Gate 4), the §4.5 thresholds were fitted to that same evidence, and no signed record or v4r4 gate carries it |
| 6 | R3 did not match §6.2 | **accepted.** Both now say: 58 of 66 current misses are on the harder side, no wider-caliper re-selection was run, so what widening would admit is unknown |
| 7 | "made its own control trivial" | **accepted.** Replaced with the observed fact — `RF11:26` at 0.6875 solo and 0.9688 composed with *B*, exceeding the registered [0.05, 0.95] ceiling — in the intro, the outline's Figure 3 row and `FIGURE_PLAN.md` |
| 8 | residual novelty precommitment | **accepted.** "The paper's contribution is methodological", "the failure is the measured contribution" and "misconception-correcting" are gone. Claim order is now justified by evidence order, and R1 defers the venue question to CITE-02/CITE-03 |
| 9 | minor wording | **accepted.** §6.1 (i) now reads "two of the four checkpoint runs"; the ladder asymmetry is a post-hoc diagnostic, not "the finding" |

## Fifth pass, 2026-08-24 — reconciliation, third round

Six residual inconsistencies. All accepted; one was resolved against the signed
records. No estimate, interval, gate outcome or evidential status changes.

| # | issue | disposition |
|---|---|---|
| 1 | §6.3's fallback contradicted `GAPS.md` G10 and red-team R10 | **accepted.** All three now say the same thing: only the two **motivating problems** — the §4.7 headroom breach and the §4.4 ladder skew — are supportable from v4r4's own records. The κ/p̂ proposal **does not survive** removal of the v5 report; v4r4 registers no such quantity and no v4r4 record carries one. G10's earlier "both points are supportable" was wrong and is corrected |
| 2 | "before generation" was ambiguous for the two attrition diagnostics | **accepted.** Now "before any composed-cell generation" in §6.4, with the contrast made explicit: composed-headroom validation needs the composed cells |
| 3 | Figure 1's planning text presupposed C2 is a contribution, and referred to "four intervals" | **accepted.** The deferral note now says what kind of contribution C2 is — or whether it is one — is unresolved pending CITE-02 **and** CITE-03. "Four intervals" was stale: the result panel carries the **twenty interval-bearing estimates** against the six estimands with none |
| 4 | Table 2 duplicated L4 per configuration | **accepted, and verified against the records.** In `payload.claims`, L1–L3 are emitted per member inside `<configuration>.statements`, while `L4` is a **sibling** of the two configuration blocks, carrying `configuration: "outcome_first\|outcome_second"` and a `levels_by_configuration` map — one classification per checkpoint run. Table 2 is now two bands: L1–L3 × run × configuration (12 rows), L4 × run (2 rows). Repeating L4 per configuration would present one classification as two results, which is the same set-versus-member confusion the emitter defect turned on |
| 5 | `01_narrative.md` said composition degradation is "not in dispute", and folded provenance into C1's contribution | **accepted.** Both removed. Whether the degradation is already established is a question pending CITE-01/CITE-03 — asserting it concedes priority nobody has checked. Provenance is reported for auditability in Appendix G and is not a scientific contribution of C1 |
| 6 | §3.2, §3.3 and §3.5 asserted facts about prior work that §3.1 was careful to leave open | **accepted.** All three now match §3.1's treatment: §3.2's symmetry claim is conditional on CITE-03, §3.3's novelty *disclaimer* on CITE-04 (a wrong citation there overclaims in the other direction, by conceding priority), and §3.5's "sparse" on CITE-07 |

## Sixth pass, 2026-08-24 — cleanup

Five residual issues, all cleanup-level rather than design-level. All accepted.
No estimate, interval, gate outcome or evidential status changes. **The
intentionally open items stay open** — G16, G17, Q9, Q11, provenance anchoring,
and CITE-02/CITE-03 are unresolved by design and were not "fixed".

| # | issue | disposition |
|---|---|---|
| 1 | `01_narrative.md`'s provenance motivation asserted that preregistration in ML "is usually asserted rather than demonstrated" — a field-level claim §3.5 now correctly leaves open | **accepted.** Made conditional on CITE-07. What survives without citation is local: in this study the device is inspectable in the artifacts. Whether that is unusual is not asserted |
| 2 | `GAPS.md` G16 said closing "any one" of the three sensitivities requires "a counterfactual re-selection" | **accepted — inaccurate as written.** Only the caliper question is a re-selection. Gate-4 strictness needs a **minimum detectable effect**; the badly-chosen-references objection needs evidence about the **excluded production-class families** (G17). G16 now carries a three-row table naming the distinct analysis each needs |
| 3 | `ITERATION.md`'s first-review strategic paragraph said that if the identification account is not novel, "v4r4 has no contribution left" — conflicting with the corrected Q8 | **accepted.** Marked **superseded** with the correction stated above it, and the two sentences that made CITE-02 the sole hinge struck through in place. CITE-02 and CITE-03 matter independently; only if *both* return known does the paragraph's reading apply. Kept for the record of what the first review argued |
| 4 | `TITLES.md` precommitted to a "methods-and-negative-result paper" whose contribution is "the identification requirement and the measured failure", deferring only to CITE-02 | **accepted.** The deferral now names CITE-02 **and** CITE-03 and spells out the four outcomes; criterion 1 says explicitly that what the contribution is cannot be fixed yet and that the methods-and-negative-result reading is the presupposition the deferral exists to suspend. The historical T1/T2/T3 discussion is unchanged |
| 5 | C1's motivation said "at least one instruction is not [delivered]" | **accepted — stronger than the estimand licenses.** `D(c←g)` is an aggregate rate difference over blocks in verifier-defined compliance, not a per-response verdict. Now: "In both position-matched cells, at least one instruction shows a detectable reduction in verifier-defined compliance", with the aggregate/categorical distinction stated |

**Audit closed at this pass.** The next step is the literature search (Q1), not
further reconciliation of the planning package.

---

## Revised open questions

**Q1 · How wide should the literature search be, and when?** *Now blocking step
4, not just §3.* Unchanged in substance, raised in priority.

**Q2 · RESOLVED — C3 is demoted.** Provenance and the commitment device are
reported in §2.7 and §6.1 and are not claimed. See the review table above.

**Q3 · SUPERSEDED.** Asked whether the first person in T1 was acceptable. The
real problem is that T1 generalises; no title is chosen. See `TITLES.md`.

**Q4 · Are qualitative response samples included?** Unchanged. *Blocking
Appendix D.*

**Q5 · Who authors the §27 codebook, and when?** Unchanged.

**Q6 · Should `02_admission_landscape.json` be added to the bundle?**
Unchanged, and now more pressing: both of C2's attrition diagnostics, the
structural-class scope restriction and every count in Figure 2 read it.

**Q7 · RESOLVED in scope.** §6.3 cites only the clean v5 file, names the
design-fitting condition, and records the v4r4-only fallback.

**Q8 · Is v4r4 a paper, or the diagnostic section of the v5 paper?** Decide after
Q1 — and note that it turns on **CITE-02 and CITE-03 together**, not CITE-02
alone. If C2's attrition account is already known but C1's directional estimand
is not, there is still a paper, and the reverse also holds.
**Reopened by v5's execution (2026-08-24).** A third reading now exists: one
paper carrying a v4r4 behavioural result *and* a v5 prospective identification
failure, which is a different and stronger object than either alone. Still
undecided, and still gated on the literature review.

**Q9 · NEW — do any of the three sensitivity analyses get run?** G16 names them:
re-selection at a wider caliper, a minimum detectable effect for the headroom
band, and any evidence that the excluded production-class families would have
supplied acceptable references. Each would convert an unresolved sensitivity into
an answer, and the third would decide whether class exclusion belongs anywhere
near the attrition story. All three are re-analyses of existing signed data, not
new generation. **Not run in this iteration**, which was instructed to compute no
estimand.

**Q10 · NEW — is the provenance chain anchored before submission?** G15. Pushing
the freeze commit costs nothing and makes the current state externally checkable
from that point forward. It does **not** convert the temporal claim, which is not
upgradable after the fact.

**Q11 · NEW — does Figure 2 plot pre-screen ι as well as calibration ι?** The
shortlist was selected on the first and the skew is measured on the second, and
17 of the 84 rungs change side between them (14 above→below, 3 below→above).
Still a rendering decision for step 4, but **recommended: show the shift in the
figure**, as 54/30 → 65/19 with the two one-way counts and the per-run
transitions, rather than confining it to the caption. A reader who sees only
65/19 will take the skew for a fixed library property, and a caption is the part
of a figure most often skipped. Plotting both is busier; the alternative hides
the single fact most likely to be over-read. `FIGURE_PLAN.md` Figure 2 constraint
3 carries the recommended rendering.

## Note on one framing correction

The task described the v5 development report as an uncommitted source.
`dci1/reports/dci1v5/reference_design_development.md` is in fact **tracked and
clean** at `3d57ad2` — `git diff HEAD` on it is empty, last committed at
`89604f6`. Other files under `dci1/reports/dci1v5/` and `dci1/src/dci1v5/` are
modified, and a citation to any of those would carry the uncommitted caveat.
§6.3 cites only the clean file. The design-fitting condition applies in full and
is unaffected.
