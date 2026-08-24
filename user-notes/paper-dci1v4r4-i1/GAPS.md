# GAPS

What is absent, and what it blocks. Seeded from the six MISSING items in
`paper/v4r4_bundle/MANIFEST.md` §5 and extended with what the outline stage
surfaced.

Severity is against **this outline and the prose draft that follows it**:
*blocking* stops a deliverable, *release* stops submission or the reproducibility
checklist but not the draft, *noted* is a limitation the paper carries.

---

## From the bundle manifest

### G1 · Gate-4 stage records for the two terminal checkpoint runs · **noted**

`GATE_4_COMPOSED_HEADROOM/records/gate4_composed.json` does not exist under
`gemma-3n-e2b-it` or `qwen3-4b-instruct-2507`; those directories hold only
`backend_runs/headroom/`. Searched: both directories in full and the same paths
under `dci1/durable_root/dci1v4r4/`.

**Blocks nothing.** A Gate-4 failure is a terminal status and the lifecycle
writes a terminal report instead of a PASS stage record. `terminal_report.json`
is signed, verifies, and carries `status`, `gate`, `band`, `failures` and a
`table` of per-cell per-slot composed rates — the content §4.7 and Figure 3
need. **Action:** §4.7 cites `terminal_report.json`, and Appendix B states in
one sentence why no Gate-4 stage record exists for those two, so a reader does
not read the absence as a lost file.

### G2 · No §27 per-variable codebook for v4r4 · **release**

Searched `find dci1 -iname '*codebook*'` — returns `dci1v3`, `dci1`, `dci1v4`
modules, no `dci1v4r4` — and `grep -rl codebook dci1/src/dci1v4r4/
dci1/reports/dci1v4r4/`. The only `codebook` in the v4r4 tree is the freeze
record's field, which holds `{"states": [...], "types": [...]}` — an
artifact-state and artifact-type vocabulary, not a per-variable codebook.

§27 requires one row per released variable with name, type, permitted values,
units, causal role and a one-sentence definition. **No such table exists.**

**Blocks:** §30 release compliance, and the NeurIPS reproducibility checklist
item on data documentation. **Does not block the draft** — every variable the
paper reports is defined in §2 and in `EVIDENCE_MAP.md`.
**Action:** author the codebook before release, covering at minimum the columns
of `per_block_cell_means.csv` and the fields of Table 1. The variable names and
types are recoverable from the bundled records and the derived CSV, so this is
authoring work, not recovery work. Owner: unassigned. See `ITERATION.md` Q5.

### G3 · No Related Work draft · **blocking for §3**

Searched `grep -rlni "related work"` over all `.md` and `.tex`. What exists:
`user-notes/paper-guides/guidelines-related-works.md` (a house guideline),
`user-notes/DCI_paper_review_packet_2026-08-20.md`, and three further
paper-guide files. None is a draft.

**Blocks:** §3 and Appendix F cannot be written past the outline stage.
**Action:** see the TODO(CITE) register below.

### G4 · No `.bib` file · **blocking for §3**

`find . -name '*.bib'` excluding `.venv` and `.git` returns **nothing**.
**Blocks:** every citation in the paper. **Action:** see below.

### G5 · No figure-generation code and no matplotlib style file · **noted**

`find . \( -name matplotlibrc -o -name '*.mplstyle' \)` returns nothing;
`grep -rl "matplotlib\|pyplot" dci1/ --include=*.py` returns nothing, so no
v4r4 figure code exists. The nearest artifacts —
`exploratory/dci_exploratory/plotstyle.py` and six `exploratory/*_figures.py` —
reference no v4r4 artifact (verified by grep) and belong to a different
constraint vocabulary.

**Blocks nothing at the outline stage**, by design: step 4 builds figures.
**Action:** author a style module at step 4 that sets `pdf.fonttype = 42` and
`ps.fonttype = 42` before anything else, per `FIGURE_PLAN.md`. Do not import the
exploratory style.

---

## Surfaced by this outline

### G6 · No registered cross-configuration or cross-model estimand · **noted, load-bearing**

v4r4 registers no contrast between configurations and none between models, and
the records store no bootstrap replicates, so no such contrast can be formed
after the fact. C1 therefore reports only that the identity of the constraint
showing a detectable loss varies across the four observed cells, read off four
separately-estimated intervals. The phrase "differs by model and by position"
was removed from the claim on review.

**Blocks:** any sentence of the form "the difference is significant".
**Action:** §5.4 and §6.1 item (iv) state that the comparison is described, not
tested. `01_narrative.md` already carries this in C1's boundary.

### G7 · No position-clean quantity survives · **noted, load-bearing**

§11.4 names `Delta_R` and `delta_difficulty` as the position-clean quantities
that carry the companion-identity claim. Both are `NOT_IDENTIFIED`. The paper
has no position-clean estimand at all.

**Action:** §5.4 says so explicitly rather than letting the reader infer it from
the `POSITION_CONFOUNDED` status alone.

### G8 · `qwen3-4b`'s `core_references` is populated on a `reduced` design · **noted**

Gate 3 selected `RF11:21` and `CR5:8` [`G3:qwen3-4b` → `core_references`] and
§8.6's reduced design never composed them, so the freeze record carries a
populated field for an estimand that is not identified. The declared exemption
`core_references → EXCESS_NOT_IDENTIFIED` for the `reduced` variant is what
governs.

**Blocks nothing.** **Action:** `EVIDENCE_MAP.md` Table 2 already records it;
Appendix B repeats it, so a reader inspecting the freeze record is not misled.

### G9 · `lifecycle_integrity.json` predates Gate 5 · **noted**

See `SCOPE_STATEMENTS.md` §4. **Action:** the boundary sentence is mandatory in
Appendix G and §6.1 item (vii).

### G10 · The v5 development material is design fitting · **noted, narrowed 2026-08-24**

> **Narrowed by v5's execution.** v5 has since been registered, frozen and run
> to close. The design-fitting condition below **still holds for the v5
> *development report***, whose thresholds were fitted to v4r4 — no sentence
> may call that validation. It does **not** describe the v5 *run*, which was
> executed under a signed registration without amendment to its scientific
> rules and is therefore prospective evidence about whether the fitted design
> works. That result is negative and is recorded in
> `04_v5_prospective_followup.md`. Cite the two separately or the paper will
> overclaim.

`dci1/reports/dci1v5/reference_design_development.md` measures five failure
modes of v4r4's reference construction and is the strongest available material
for §6.3. Every threshold in it was chosen after observing all of v4r4.

**Constraint:** no sentence in the paper may call it validation.
**Correction to the working assumption:** this specific file is **tracked and
clean** at commit `3d57ad2` — `git diff HEAD` on it is empty and its last commit
is `89604f6` — so the "uncommitted source" caveat does not apply to it. Other
files under `dci1/reports/dci1v5/` and `dci1/src/dci1v5/` *are* modified, and a
citation to any of those would carry the caveat. §6.3 cites only the clean file.
**Fallback if a reviewer objects to any v5 use — and its limit.** Only the two
**motivating problems** are supportable from v4r4's own attrition records: the
§4.7 headroom breach and the §4.4 ladder skew. The **κ(R│B) / p̂ proposal does
not survive the removal** — v4r4 registers no such quantity, no v4r4 record
carries one, and the report's own §4.5 thresholds were fitted after observing all
of v4r4. Earlier wording here said "both points are supportable", which was
wrong: the motivating problems and the proposed remedy are not interchangeable.
§6.3 and red-team R10 now say so.

### G11 · `SCIENTIFIC_FOLLOWUP_EVIDENCE.md` §6 carries a confirmed error · **noted**

Lines 491–492 give `REFERENCE_CALIPER` 0.075 and `REFERENCE_PRESCREEN_CALIPER`
0.10. The registered values are 0.10 and 0.15
[`dci1/src/dci1v4r4/protocol/constants.py:233,235`;
`02_admission_landscape.json` → `thresholds`]. `0.075` never entered any
selection: `dci1v4r4/stages/selection.py` reads the constants module at lines
247 and 259. The value appears nowhere in this paper.

**Action:** Appendix H records it as a reproduction trap. The paper cites the
follow-up report for its *diagnostics*, never for a threshold.

### G12 · Four stale constants in `dci1v4r4` · **noted**

`N_SEVERITIES` (`verifiers/constraints.py:463`, comment `# 190`, computed 254),
`N_DECLARED_SEVERITIES` (`:464`, `# 334`, computed 510), `N_CONFIRMATORY`
(`protocol/constants.py:50`, `# 408`, computed 384), `N_SEQUESTERED` (`:51`,
`# 72`, computed 96). Only `N_CONFIRMATORY` reaches a reported number, by value,
as `blocks: 384`.

**Action:** library-size figures come from `coverage.json` or
`gate1_decision.json`, never from a constants module. Already enforced in
`EVIDENCE_MAP.md` §Numbers explicitly excluded.

### G13 · `02_admission_landscape.json` is a post-hoc diagnostic · **noted**

Both of C2's attrition diagnostics, the structural-class scope restriction and
Figure 2 read it. Its own `_provenance` says the verdicts
were computed by the registered `stages.selection` functions on the signed
Gate-2 table, so the verdicts are not reimplemented — but the *artifact* is
post-hoc and this paper labels it so, per
`guidelines-narrative-and-process.md` on marking pre-specified versus post-hoc
analyses.

**Action:** §4.3–§4.5 and Figure 2's caption carry the label. The primary
outcomes it summarises — `core_references`, `dropped_for_no_triple`,
`design_variant` — are also on the signed Gate-3 records and are cited there.

**A second property of this file that must travel with its counts.** It holds
only the **shortlisted** rungs — the six budget-class families §12.3 carried to
Gate-2 calibration on each checkpoint run, 21/20/23/20, 84 pooled — not the 254
eligible rungs the pre-screen measured per run. And its `iota` is the Gate-2
calibration value while the shortlist was chosen on `prescreen_iota`: on the same
84 rungs the pre-screen split is 54 below / 30 above ι_A against 65 / 19 at
calibration — **14 moving above→below and 3 below→above, 17 changing side**, for
a net 11; 51 stayed below and 16 stayed above. Any use of 65/84 states what the
84 are and carries that caveat;
`EVIDENCE_MAP.md` Table 3 rows 2d–2g hold the derivation.

### G14 · No decision on qualitative samples · **blocking for Appendix D**

`guidelines-methods.md` requires the selection protocol to be stated before any
sample appears, and `guidelines-appendix.md` puts the protocol in the main body.
No protocol is registered and no sample is currently planned.

**Action:** decide at step 4. If none is included, delete Appendix D rather than
shipping it near-empty. See `ITERATION.md` Q4.

### G15 · No external anchor for the provenance chain · **noted; partly fixable, and only forward**

The signing key is at `dci1/evidence/dci1v4r4/keys/signing.key`, 64 bytes, mode
0600, **gitignored and untracked**, so it is not distributed. But HMAC under a
symmetric key held by the researcher establishes integrity **only against parties
without the key** — not authorship, and not temporal precedence, since a
key-holder can produce a valid HMAC over any content at any time. And the freeze
commit `450a049` is **on no remote ref** (`git branch -r --contains 450a049`
returns nothing; `HEAD` is 115 commits ahead of `origin/main` at `3c14d66`), so
no external immutable anchor exists for the chain.

**Blocks nothing in the draft.** **Action:** state exactly what the signatures do
and do not establish (`SCOPE_STATEMENTS.md` §6), and — if wanted before
submission — push the freeze commit or publish a timestamped digest of the freeze
and masked records. **That anchors the state from the moment of publication
forward and is worth doing; it cannot retroactively establish that the records
existed before unmasking.** The temporal claim is not upgradable after the fact,
so the scope sentence in `SCOPE_STATEMENTS.md` §6 stands either way.

### G16 · No sensitivity analysis behind the three alternative-explanation answers · **noted, load-bearing**

§6.2 raises three objections — badly chosen references, too tight a caliper, too
strict a Gate 4 — and closes none of them by analysis. No
re-selection at a wider caliper was run, no minimum detectable effect was
computed for the headroom band, and registered selection rules out cherry-picking
without showing the rule was good.

**Blocks:** presenting any of the three as a rebuttal. **Action:** they are
written as unresolved sensitivities. Closing any one requires an additional
sensitivity or counterfactual analysis this study did not run and this iteration
must not invent — and the three need **different** analyses, not one:

| objection | what would close it |
|---|---|
| "the caliper was too tight" | a **re-selection** at a wider caliper, to measure what widening actually admits |
| "Gate 4 was too strict" | a **minimum detectable effect** for the [0.05, 0.95] headroom band |
| "the references were badly chosen" | evidence bearing on the **excluded production-class families** — whether they would have supplied acceptable references (`GAPS.md` G17) |

Calling all three "a counterfactual re-selection" was wrong; only the first is
one.

### G17 · No counterfactual linking the attrition diagnostics to non-identification · **noted, load-bearing**

C2 reports two post-hoc diagnostics of reference attrition. **No ablation shows
that relaxing either would have made `Delta_R` identifiable.** In particular
nothing shows the excluded production-class families would have supplied
acceptable references.

**Action:** the diagnostics are labelled descriptive throughout; the registered
gate outcomes carry the causal weight.

**Partially answered by v5, prospectively (2026-08-24), and not in the
direction an ablation would have gone.** v5 registered a design built on these
very diagnostics — a strengthened reference construction, and a support
criterion (§12.6 C4) whose "three spare" margin was set from v4r4's measured
50–100% attrition — froze it, and ran it. **Identification still did not
survive**: three of four replications failed C4 (4, 5 and 5 qualifying
straddling feature groups against a registered 6) and recorded irreversible D6
non-identification; the fourth kept identification and then failed the
independent composed-headroom gate. So a design informed by these diagnostics
was tried prospectively and did not deliver `Delta_R`.

**What this does and does not close.** It supplies the missing prospective
counterfactual in the only form actually available — a registered attempt —
and it separates reference-support failure from composed-headroom failure as
distinct sequential bottlenecks, which v4r4 could not do. It does **not** show
that relaxing either v4r4 diagnostic would have made `Delta_R` identifiable
(no such ablation exists, and none is licensed post hoc), and it does **not**
show that matched-companion identification is impossible in general. The gap
narrows; it does not close. `04_v5_prospective_followup.md`.

---

## TODO(CITE) — the citation verification register, seeded

The repository contains **no `.bib` file and no prior Related Work draft**, so
every citation in this paper is unverified until checked against a primary
source. Per `guidelines-appendix.md`, unverified citations stay in the
bibliography, are flagged `TODO(CITE)` at the point of use, and are listed in
Appendix E with the claim they support, whether it is load-bearing, what was
checked, and what remains unverified.

| id | claim it would support | load-bearing? | status |
|---|---|---|---|
| CITE-01 | The field-level framing of instruction-following and multi-constraint compliance (§1 ¶1) | no — context | unverified; no source consulted |
| CITE-02 | Prior constraint-composition benchmarks measure aggregate compliance as instruction count rises, and none forms a companion-replacement contrast (§3.1) | **yes** — carries C2's novelty | unverified; **this is the single most important citation in the paper** |
| CITE-03 | Pairwise interaction statistics in prior work are symmetric co-failure or correlation measures (§3.2) | **yes** — carries C1's estimand delta | unverified |
| CITE-04 | Position and ordering effects in multi-constraint prompts are already reported (§3.3) | **yes** — the paper *disclaims* novelty here, so a wrong citation would overclaim in the other direction | unverified |
| CITE-05 | Construct validity in benchmark measurement; the requirement that additional subtasks must not confound the measurement (§3.4) | yes — the framing C2 operationalises | unverified. A candidate exists in the repository's own memos (Bean et al. 2025, arXiv:2511.04703, cited in `user-notes/DCI-1_preregistration_v3.md:885`), and must be read at source before use |
| CITE-06 | Shortcut learning as the frame for verifier-satisfiable-without-the-intended-behaviour (Appendix H, optional) | no | unverified. Candidate in `user-notes/short-cuts-1.txt:1008` (Geirhos et al. 2020, arXiv:2004.07780); read at source before use |
| CITE-07 | Preregistration practice in ML (§3.5) | no — context only, now that provenance is not claimed | unverified |
| CITE-08 | Block bootstrap and studentised maximum-modulus simultaneous intervals (§2, §5.2) | yes — method attribution | unverified; standard, but must be attributed precisely |
| CITE-09 | Newcombe intervals for the difference of two proportions (§2.5, §4.5) | yes — method attribution | unverified |
| CITE-10 | Šidák multiplicity correction (§5.2) | yes — method attribution | unverified |

**Two rules for this register**, both from the guideline. Recent work is
verified against the source document rather than an intermediate summary,
because inherited errors in this area have been substantive. And a citation that
cannot be verified is flagged, never dropped — dropping it destroys the trail.

**Workflow consequence, added on review.** The literature search is not a §3
task to be done last. C2's standing as a publication-level contribution rests
entirely on CITE-02, so the search comes **before** Figure 1 is built and before
a title is chosen. If prior work has already encountered reference-construction
or matching failures of this kind, C2's framing changes and Figure 1 changes with
it. Step 4 of the writing process is therefore blocked, not merely unstarted.

**Scope decision needed:** how wide the search should be. See `ITERATION.md` Q1.
