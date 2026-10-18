# DCI — current scientific state

The 10-minute orientation. Everything here points at something else; primary
numbers live in the reports and the generated artifacts, not in this file.

Last reviewed: 2026-09-13.

---

## 1. The question

Does adding instruction **B** to a prompt causally degrade compliance with
instruction **A**, over and above the generic cost of one more instruction?

The design removes that confound by *replacement* rather than addition — compare
a composition containing B against one where B is swapped for a comparable
reference R, holding the background set S and the instruction count fixed:

```
A + B + S     versus     A + R + S
τ(B→A | S,R) = P(fail A | A+B+S) − P(fail A | A+R+S)
```

Positive τ is directional interference.

## 2. Two arms, different rules

| | `src/dci/` + `configs/` + `notebook_source/` | `exploratory/` |
|---|---|---|
| what | the preregistered v15/v19 protocol | fast, cheap, local-GPU probing |
| changes | ledgered amendments (`docs/migration_ledger.csv`, `src/dci/v19/stage2_frozen.json`) | free; interfaces break by design |
| output | a **gate status**, not a number (`src/dci/statuses.py`) | estimates stamped `EXPLORATORY_NO_EVIDENCE` |
| status | **Paused.** Stage 2 frozen, with Pair 3 segmentation and the verifier implementation hashes re-frozen on 2026-09-13 and Pair 3's section 10.6 semantic re-audit outstanding; the confirmatory run has **not** been executed | eleven rounds completed |

They are coupled in one direction: `exploratory/dci_exploratory/harvest.py`
executes confirmatory stages `c112…c212` at runtime to obtain the constraint
definitions, wordings, verifiers and task bank, so the exploratory arm invents no
scientific content — and a change in `src/dci/` changes what an exploratory design
means. Each run records the definition hashes it used.

`dci1/` is a third area and a separate study, DCI-1 (§4b), with its own
preregistrations, code and evidence. **DCI-1 v8.1 is the active study line** and
has completed its frozen confirmatory run and analysis. The v19 protocol above
is a different study, currently paused; v8.1 does not supersede it.

## 3. Experiment families

Eleven, indexed with entrypoints, analysis code, reports and per-family status in
**[`exploratory/EXPERIMENTS.md`](exploratory/EXPERIMENTS.md)**.

## 4. What is currently believed

Scope for essentially all of it: one target/focal pair, the Qwen3-4B lineage,
20 pilot tasks, exploratory inference. Full ledgers with evidence and limitations
in [`exploratory/CLAIM_EVIDENCE_MATRIX.md`](exploratory/CLAIM_EVIDENCE_MATRIX.md)
and [`exploratory/HYPOTHESES.md`](exploratory/HYPOTHESES.md).

- **The effect is real but not pair-specific.** Certain added instructions cause
  large target failure that matched references do not — but the registered focal
  B has essentially no effect on its own. Its effect is a higher-order interaction
  with the background. *(`FINDINGS.md`, `ROUND5_REPORT.md`)*
- **The failure has a shape.** The model satisfies a punctuation demand by writing
  one multi-clause sentence, destroying the unit the target counts. *(`METRIC_SPEC.md`)*
- **The trigger is a property of the instruction, not the output.** Emission of
  the mark does not track the effect; receiving the instruction does.
  *(`AMPLIFIER_MECHANISM_MATRIX.md`)*
- **Leading mechanism: clause-boundary affordance.** Marks that can stand where a
  sentence boundary stands amplify; matched marks that cannot do not. Supported
  predictively; the causal crossing was designed and **not run**.
  *(`BOUNDARY_MECHANISM_REPORT.md`)*
- **Order is a treatment.** The same instructions span amplification to reversal
  depending on order. No simple positional rule survives. *(`CLAIM_EVIDENCE_MATRIX.md`)*
- **Reasoning re-prioritises; it does not compose.** Thinking removes the
  control-context interference but leaves the amplified context largely intact,
  and joint satisfaction stays rare. Explicit priority cues are attended to in the
  traces and do not change the answer. *(`NATURAL_REASONING_RESULTS.md`, `ROUND11_ARBITRATION_REPORT.md`)*
- **Transport decomposes.** The disposition is universal; the arbitration is
  checkpoint-specific. On 2026 checkpoints the target saturates, so τ = 0 − 0 by
  construction — a structural zero, never a behavioural null.
  *(`ACTUAL_CROSS_MODEL_DCI_RESULTS.md`)*
- **The execution condition is part of the result.** Checkpoint+revision, backend,
  dtype, chat template, reasoning mode, decoding, seeds, parser and answer
  extraction. Results from materially different conditions are reported side by
  side, never pooled. *(`CROSS_MODEL_EXECUTION_MATRIX.md`)*

## 4b. DCI-1: the registered study line

`dci1/` is a separate, isolated study module with its own preregistrations and
its own evidence tree. It does not share code with `src/dci/` or
`exploratory/`.

**Current line: v8.1**, frozen on 2026-09-08 and analysed on 2026-09-10 (the
result is below this section; its development history is §4d). It is not a
successor to the v19 protocol in `src/dci/v19/` (§2), which is a separate,
paused study.

**Where the code is.** The authoritative code for every DCI-1 revision, v8.1
included, is on `main`; the development branches named in the dated sections
below (`dev/v8-canonical`, `dev/v8-frame-aware-prescreen`,
`dev/v7-difficulty-spectrum`) have been merged into it.

**What evidence a clone carries.** Raw stage records are not in git:
`dci1/evidence/` is gitignored, and the repository records no off-machine
archive of it. For v8.1 the durable references are the committed ones: the
preregistration `dci1/docs/DCI1_preregistration_v8.1.md` and the freeze commit
`034fc72`; the tables projected from the signed confirmatory records,
[`dci1/reports/dci1v8dev/postconfirm/data/`](dci1/reports/dci1v8dev/postconfirm/data/),
whose `provenance.json` carries each signed record's hash and its signature
verification; and the audits in `dci1/reports/dci1v8dev/postconfirm/audits/`,
which authenticate all 2,353,152 scored rows in 168 backend runs against the
signed generation records and replay all 56 executed `delta_difficulty`
bootstraps. A clone can check every reported number against those tables and
see which signed record each came from. Re-verifying the tables against the
records themselves needs the raw root.

**The author's local raw copy.** The raw roots exist only on the machine that
ran the study, which is also where the absolute paths inside `provenance.json`
and the audits point. There, the v8 and v8.1 roots (`dci1v8-pilot*`,
`dci1v8-confirm*`, `dci1v8p1-confirm`) sit in a sibling worktree,
`../dci-v8-canonical`, a checkout of `main` kept because it holds them, and the
roots of earlier revisions sit in the primary checkout's `dci1/evidence/`.
Neither location exists in a fresh clone or in CI.

| Version | Status |
|---|---|
| v2 | closed |
| v3 | closed. Two Gemma replications reached UNMASKED_ANALYSIS; both Qwen replications terminated at Gate 2A. `dci1/RESULTS_V3.md` |
| B+R pilot | non-confirmatory design evidence for v4. `dci1/reports/br_pilot_v4/` |
| **v4r2** | **implemented, not frozen, no confirmatory data**, terminal at Gate 2 as registered. `docs/v4_traceability.md`, `dci1/docs/v4_prefreeze/` |
| **v4r3** | **closed 2026-08-21, terminal at `GATE_1_MEASUREMENT`, no confirmatory data.** Adopted and registered, run through stage 3, and stopped where its registered criterion stopped it: §18 stage 4 required §10.2 plus §10.3 or §10.4, and neither pathway established that basis. Superseded by v4r4; its evidence is preserved unedited and its closure is hashed. §4h–§4l, §4m. `user-notes/DCI1_preregistration_v4r3.md`, `dci1/reports/dci1v4r3/closure.json` |
| **v5** | **RUN AND CLOSED 2026-08-24. No replication reached `CONFIRMATORY_GENERATION`: two terminated at Gate 4 on §13.14 composed headroom, two are permanently blocked at `PREFREEZE_AUDIT` by an irreversible D6 non-identification. 459,312 behavioural rows exist and none is confirmatory.** [`dci1/reports/dci1v5/CLOSURE.md`](dci1/reports/dci1v5/CLOSURE.md) All nineteen §34 decisions closed, U2 resolved at A2, P1 confirmed, registration manifest signed; three closures went against the document's own standing proposal (D16, D17, D18). The registered design is five arms, four models, 56 cells, 1,172,544 generations. A standalone preregistration that rebuilds the reference-construction procedure v4r4 could not make work. The core reference pool inverts to production class and same-form with A; ι is demoted from the admission coordinate to the difficulty coordinate; a pre-composition interaction gate, two calibration splits, direct order estimands and the L4 fix are new. Its execution plumbing has been exercised end to end on synthetic fixtures, which is engineering evidence and not a result. A stage 3–18 execution-path audit then found twelve registered rules that the production path did not execute — four multiplicity families with no producer, three claim emitters with no caller, §12.6's expansion unreachable and its coverage criterion evaluated on an empty set — and one place, §12.6's eligibility predicate, where the preregistration did not determine the rule. That one was resolved at E2 — §13's band applied to the quantity §13 bands, $p_{\text{solo}}$ — and §18 step 14's raw-coordinate fit was implemented as §15 registers it, with no multiplicity family invented. 48 registered rules are now audited against the path a replication takes, all 48 reachable, over 15 conditional scenarios. §4q, §4r, §4s, §4t, §4u, §4v, §4w, §4x. [`user-notes/DCI1_preregistration_v5.md`](user-notes/DCI1_preregistration_v5.md), [`dci1/src/dci1v5/`](dci1/src/dci1v5/), [`dci1/reports/dci1v5/`](dci1/reports/dci1v5/) |
| **v6** | **RAN AND CLOSED 2026-08-27, zero survivors of four (§4ak).** `qwen3-4b` and `qwen3-4b-instruct-2507` terminated at Gate 2.75 `COMPOSED_HEADROOM_UNREACHABLE` because **B's compliance rose under A toward the ceiling** (0.747 → 0.891; 0.779 → 0.924); `gemma-3n-e4b-it` at Gate 4 `COMPOSED_HEADROOM_FAILURE` on `solo:CL` = 0.958, a companion's own solo cell; `gemma-3n-e2b-it` passed Gate 4 and terminated at `PREFREEZE_AUDIT` because A16/A17 had edited the registered document and the lifecycle could not bind a post-registration amendment. Both Gemmas had lost `Delta_R` at Gate 3C. All four verdicts stand. [`dci1/reports/dci1v6/CLOSURE.md`](dci1/reports/dci1v6/CLOSURE.md). *Registration history:* ADOPTED and REGISTERED 2026-08-26 (registration after amendment A15; §4ah). Zero behavioural rows at registration. All twenty-seven §34 decisions and all three blocking §33 items closed on [`dci1/reports/dci1v6/researcher_decisions.json`](dci1/reports/dci1v6/researcher_decisions.json); D0–D18 carried at v5's actually adopted values with v5's evidence and a `carried_from` block. Nineteen stages: a new `GATE_2_75_COMPOSED_PROBE` measures composed headroom at the **frozen** m\* two stages before Gate 4 and may terminate a replication `COMPOSED_HEADROOM_UNREACHABLE` but may never move the operating point. V6-E01/E02/E05 repair §12.6's reachability, expansion-row eligibility and `n_stable` prospectively. Three `probe_only` families PS1–PS3 are non-selectable by construction. §34 D23 = `projection_sd`, D26 = 0.0142 (measured). Registered design: five arms, four models, 56 cells, 1,174,080 generations. §18 stage 1's `REGISTRATION_INCOMPLETE` is a **readiness refusal**, not a §28 terminal status (A15); §12.6 drops a rung with no difficulty coordinate from its coverage conditions and records it (A16). Executing: all four registered, qualified and through Gate 1; §4aa–§4aj. [`user-notes/DCI1_preregistration_v6.md`](user-notes/DCI1_preregistration_v6.md), [`dci1/src/dci1v6/`](dci1/src/dci1v6/), [`dci1/reports/dci1v6/`](dci1/reports/dci1v6/) |
| **v7** | **ADOPTED, REGISTERED AND RUN 2026-08-28; CLOSED the same day with zero survivors of four (§4am).** Every replication passed the stages v7 changed — both Qwens the composed probe, both Gemmas Gate 4 — and every one lost `Delta_R` at Gate 3C on §12.6's C4 under the calibrated re-read, then ended `PREFREEZE_AUDIT_FAILURE` on `support_satisfied`. Drafted 2026-08-27 (§4ak); §13.14 boundary-audited 2026-08-28 and revised as V10 before adoption (§4al). A superseding registration, not a v6 amendment: v6's §32.3 froze §13 from the first Gate-2.5 record and §32.1 forbids weakening a criterion so that a gate passes. v7 **withdraws** the absolute composed-headroom criterion as a terminal requirement — `COMPOSED_HEADROOM_FAILURE` and `COMPOSED_HEADROOM_UNREACHABLE` leave the vocabulary and no module can raise them — and replaces it with readings of the **contrast**: a structural zero licenses nothing, an arm at an exact boundary widens the decision interval by the Wilson allowance in the open direction, and a direction compressed below the SESOI by the other arm's level is named on the statement. Gate 2.75 and `GATE_4_COMPOSED_CONTRAST` record the paired contrasts by the confirmatory estimators, bootstrapped over topics, and have one outcome. No threshold moves; the estimand layer is byte-identical to v6's. A post-registration amendment is now bindable (A4), the hole that ended `gemma-3n-e2b-it`. [`user-notes/DCI1_preregistration_v7.md`](user-notes/DCI1_preregistration_v7.md), [`dci1/src/dci1v7/`](dci1/src/dci1v7/), [`dci1/reports/dci1v7/READINESS.md`](dci1/reports/dci1v7/READINESS.md) **Amended in place 2026-08-28 (A6–A8, §4an) after the closure:** the pre-freeze check that ended every replication (`support_satisfied`, "support met") is withdrawn for the registered invariant (support *recorded*, D6's disposition, the exact non-identified set, the arm set, no rehabilitation path); §12.6's C2/C4 now gate the spectrum arm and C1/C3/C5/C6 the core arm, no value moving; D6 means one thing everywhere. Bound via the A4 chain; V11–V13 checked; the four terminal reports stand; re-running is an open researcher decision. **2026-08-29 (§4ao):** the §13.11 chance column had been 0.0 on every replication; corrected on the Gate-2 producer (V14), stored tables not comparable with corrected ones, no record re-verdicted. |
| **v4r4** | **adopted 2026-08-21; frozen at Gate 5 on 2026-08-22 for two of four replications, confirmatory data in hand.** Superseded by v5. Gate 1 is deterministic-measurement by construction (§10.7 A–E) and `CP4`/`CP7` are removed. All four replications passed Gates 1–3; **§13.10 then ended two of them at `COMPOSED_HEADROOM_FAILURE`, including the only full-design replication**. Two survive to Gate 5, both on §8.6's 8-cell reduced design, so no spectrum-dependent estimand is identified anywhere in the study. Both survivors froze at `450a049`, generated 24,576 rows each, and are analysed through `UNMASKED_ANALYSIS`; **they disagree qualitatively** and one replication's L4 field is invalidated. §4m, §4n, §4o, §4p. `user-notes/DCI1_preregistration_v4r4.md`, `dci1/reports/dci1v4r4/final_results.json` |
| **v8** | **Frozen 2026-09-03 at `f7af7f2` (root `dci1v8-confirm-r2`); confirmatory generation never started.** A frame-conditioned redesign of DCI-1, not a replication of v7. An earlier freeze (`dci1v8-confirm`, 2026-09-02) was superseded by the pre-freeze audit the same day; its partial generation was stopped, uninspected and never analysed. The frozen root is superseded for the successor design only and is untouched. §4d. [`dci1/docs/DCI1_preregistration_v8.md`](dci1/docs/DCI1_preregistration_v8.md) |
| **v8.1** | **The current line. Frozen 2026-09-08 at `034fc72` (root `dci1v8p1-confirm`), 2,353,152 rows generated, and the frozen `CONFIRMATORY_ANALYSIS` and `FINAL_REPORT` run once on 2026-09-10, returning `PASS` for all four models.** 23 of 24 joint decision intervals for Δ_R(f) stop below +10 pp; gemma-3n-e4b-it with B second is `FRAME_HETEROGENEOUS`. A post-confirmatory review (2026-09-13) found two gaps in the frozen analysis code that did not affect the executed run (`CHANGES_SCIENTIFIC.md`). §4d. [`dci1/docs/DCI1_preregistration_v8.1.md`](dci1/docs/DCI1_preregistration_v8.1.md), [`manuscript/V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md`](manuscript/V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md) |

v4r2 replaces target failure with the per-constraint compliance vector, makes
reciprocal delivery loss the primary estimand, matches references to A on solo
compliance rather than to B on solo failure, and makes instruction order a
cell-level factor. It is a different protocol: v3 and v4 numbers are not
comparable and are never compared. Nine registered open decisions (V1 to V9)
and seven pre-freeze checks remain open; the freeze and confirmatory generation
are implemented and deliberately not executed. **v8.1 (§4d) is the current
line.** It succeeds v8 (frozen 2026-09-03, never generated), the frame-conditioned
redesign that followed v7 (§4ak–§4an, closed 2026-08-28). v7 superseded v6
(§4ag–§4aj, closed 2026-08-27), which superseded v5, which superseded v4r4.
v4r4 supersedes v4r3, which superseded v4r2. Each was adopted and registered on 2026-08-21, and each is structurally prevented from reading
the others' artifacts: `dci1v4r4.engine.context.foreign_roots` names v4r3's
evidence, durable and source trees, and `assert_own_study` refuses a stage
record whose `study_id` is another revision's. No v4r2 and no v4r3 record was
edited by any of it.

### The v8.1 result (copied verbatim from §4d's last paragraph)

**FROZEN, GENERATED AND ANALYSED (2026-09-10).** The v8.1 confirmatory root
`dci1/evidence/dci1v8p1-confirm` froze at commit `034fc72` (preregistration
hash `d3552f9f…`, membership lock `31af521c…`), generated 2,353,152 rows
across 12 LOCAL and 14 SPECTRUM frames at 384 blocks per frame, and the
frozen `CONFIRMATORY_ANALYSIS` and `FINAL_REPORT` stages ran once and
returned `PASS` for all four models. **Δ_R(f) runs −11.19 to +12.64 pp over
the 24 entering model × frame × order cells; 23 of 24 joint decision
intervals stop below +10 pp (`L3c`) and the precision precondition is met in
24 of 24 (half-widths 1.05–3.24 pp).** Seven of eight model × order
configurations return `LOCAL_EQUIVALENT_SAME_FORM_ONLY`; gemma-3n-e4b-it
with B second returns **`FRAME_HETEROGENEOUS`**, because its frame 1 gives
Δ_R = +12.64 pp, joint CI [+9.62, +15.66], reading `INDETERMINATE@0.10`.
That cell is also the study's most reference-sensitive: across the nine
admissible triples of its five frozen families Δ_R runs −8.63 to +12.64 pp
and the frozen triple is the most harmful of the nine; the graded recoding
takes it to +7.07 pp; §17.4's both-bounds rule withholds its levels; and the
SPECTRUM arm on the same rows puts A 11.49 pp *below* what companions of its
measured difficulty predict. Reference-set choice changes a registered
verdict on 2 of 24 cells (both on gemma-3n-e4b-it, B second); the runner-up
operating point changes **none**. Raw composition is undiminished: D(B←A)
runs −13.5 to +49.2 pp and D(A←B) −36.1 to +54.5 pp. §26 methodological
success is `MET` on both Gemmas and `NOT_MET` on both Qwens, on D(A←B)'s
precision alone — every Δ_R interval meets its precondition. Full result
matrix, sensitivities, claim ledger and the manuscript rewrite map:
[`manuscript/V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md`](manuscript/V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md)
and [`manuscript/POSTCONFIRM_EXEC_SUMMARY.md`](manuscript/POSTCONFIRM_EXEC_SUMMARY.md); the
machine-readable tables are under
`dci1/reports/dci1v8dev/postconfirm/data/`.

## 4c–4ao. Dated study log (moved)

The dated entries that followed here — how each revision from v4r3 to v8.1 was
designed, run, audited and closed — are now in
[`docs/history/research_state_log.md`](docs/history/research_state_log.md),
verbatim and with their section numbers unchanged, so a citation of the form
"`RESEARCH_STATE.md` §4f" still means that entry. Two numbers were used twice
and both entries are kept.

| § | entry | dated |
|---|---|---|
| §4d | [The canonical v8 candidate (2026-08-29, branch `dev/v8-canonical`)](docs/history/research_state_log.md#4d-the-canonical-v8-candidate-2026-08-29-branch-devv8-canonical) | 2026-08-29 |
| §4c | [The reference-pool tension, and what was screened against it (2026-08-20)](docs/history/research_state_log.md#4c-the-reference-pool-tension-and-what-was-screened-against-it-2026-08-20) | 2026-08-20 |
| §4d | [The focal grid, and Gate 1's §10.2 evidence (2026-08-20)](docs/history/research_state_log.md#4d-the-focal-grid-and-gate-1s-102-evidence-2026-08-20) | 2026-08-20 |
| §4e | [The Gate-2 calibration screen, and what it settles (2026-08-20)](docs/history/research_state_log.md#4e-the-gate-2-calibration-screen-and-what-it-settles-2026-08-20) | 2026-08-20 |
| §4f | [The pairwise-matrix screen: Δ_R is small, and three nuisance channels are larger (2026-08-20)](docs/history/research_state_log.md#4f-the-pairwise-matrix-screen-δ_r-is-small-and-three-nuisance-channels-are-larger-2026-08-20) | 2026-08-20 |
| §4g | [The endpoint: a researcher decision boundary, and §13.2 is not part of it (2026-08-20)](docs/history/research_state_log.md#4g-the-endpoint-a-researcher-decision-boundary-and-132-is-not-part-of-it-2026-08-20) | 2026-08-20 |
| §4h | [v4r3: adopted, registered, and run to the regime screen (2026-08-21)](docs/history/research_state_log.md#4h-v4r3-adopted-registered-and-run-to-the-regime-screen-2026-08-21) | 2026-08-21 |
| §4i | [v4r3 stage 3: the stem works, and the spectrum is identified on one model of four (2026-08-21)](docs/history/research_state_log.md#4i-v4r3-stage-3-the-stem-works-and-the-spectrum-is-identified-on-one-model-of-four-2026-08-21) | 2026-08-21 |
| §4j | [v4r3's repair pass: provenance, the stage machine, and §10.4-R (2026-08-21)](docs/history/research_state_log.md#4j-v4r3s-repair-pass-provenance-the-stage-machine-and-104-r-2026-08-21) | 2026-08-21 |
| §4k | [v4r3: R3 restores coverage, R2 fails, and Gate 1 is blocked on §10.3 alone (2026-08-21)](docs/history/research_state_log.md#4k-v4r3-r3-restores-coverage-r2-fails-and-gate-1-is-blocked-on-103-alone-2026-08-21) | 2026-08-21 |
| §4l | [§10.7-R5 replaces Gate 1's measurement criterion, and the amended gate fails on a wording](docs/history/research_state_log.md#4l-107-r5-replaces-gate-1s-measurement-criterion-and-the-amended-gate-fails-on-a-wording) |  |
| §4m | [v4r4: v4r3 closes at Gate 1, and a revision whose Gate 1 is deterministic passes it (2026-08-21)](docs/history/research_state_log.md#4m-v4r4-v4r3-closes-at-gate-1-and-a-revision-whose-gate-1-is-deterministic-passes-it-2026-08-21) | 2026-08-21 |
| §4n | [v4r4 Gates 2 and 3: all four replications pass, and the spectrum is identified on one (2026-08-22)](docs/history/research_state_log.md#4n-v4r4-gates-2-and-3-all-four-replications-pass-and-the-spectrum-is-identified-on-one-2026-08-22) | 2026-08-22 |
| §4o | [v4r4 Gate 4: the composed-headroom predicate ends two replications, one of them the only full design (2026-08-22)](docs/history/research_state_log.md#4o-v4r4-gate-4-the-composed-headroom-predicate-ends-two-replications-one-of-them-the-only-full-design-2026-08-22) | 2026-08-22 |
| §4p | [v4r4 confirmation: two replications freeze, generate, mask, unmask and analyse — and they disagree (2026-08-22)](docs/history/research_state_log.md#4p-v4r4-confirmation-two-replications-freeze-generate-mask-unmask-and-analyse--and-they-disagree-2026-08-22) | 2026-08-22 |
| §4q | [v5: drafted, and what v4r4's failure was measured to be (2026-08-22)](docs/history/research_state_log.md#4q-v5-drafted-and-what-v4r4s-failure-was-measured-to-be-2026-08-22) | 2026-08-22 |
| §4r | [v5 implemented, and what running the carried code over a new library found (2026-08-22)](docs/history/research_state_log.md#4r-v5-implemented-and-what-running-the-carried-code-over-a-new-library-found-2026-08-22) | 2026-08-22 |
| §4s | [v5's execution plumbing exercised end to end, and eleven defects that only appear when a stage runs (2026-08-22)](docs/history/research_state_log.md#4s-v5s-execution-plumbing-exercised-end-to-end-and-eleven-defects-that-only-appear-when-a-stage-runs-2026-08-22) | 2026-08-22 |
| §4t | [Four §34 decisions taken, the Calibration-B bank authored, and what each remaining decision now asks (2026-08-22)](docs/history/research_state_log.md#4t-four-34-decisions-taken-the-calibration-b-bank-authored-and-what-each-remaining-decision-now-asks-2026-08-22) | 2026-08-22 |
| §4u | [v5 adopted and registered, and the estimator defect closing D17 surfaced (2026-08-23)](docs/history/research_state_log.md#4u-v5-adopted-and-registered-and-the-estimator-defect-closing-d17-surfaced-2026-08-23) | 2026-08-23 |
| §4v | [The registered study could not be executed as committed, and the registration was superseded before Stage 2 (2026-08-23)](docs/history/research_state_log.md#4v-the-registered-study-could-not-be-executed-as-committed-and-the-registration-was-superseded-before-stage-2-2026-08-23) | 2026-08-23 |
| §4w | [The registered rules of stages 3–18 were audited against the path a replication takes, and twelve were not on it (2026-08-24)](docs/history/research_state_log.md#4w-the-registered-rules-of-stages-318-were-audited-against-the-path-a-replication-takes-and-twelve-were-not-on-it-2026-08-24) | 2026-08-24 |
| §4x | [§12.6's eligibility rule was resolved at E2, §18 step 14's raw-coordinate fit was implemented as §15 registers it, and v5 re-registered (2026-08-24)](docs/history/research_state_log.md#4x-126s-eligibility-rule-was-resolved-at-e2-18-step-14s-raw-coordinate-fit-was-implemented-as-15-registers-it-and-v5-re-registered-2026-08-24) | 2026-08-24 |
| §4y | [v5 ran, and no replication reached confirmatory generation](docs/history/research_state_log.md#4y-v5-ran-and-no-replication-reached-confirmatory-generation) |  |
| §4z | [V5-E32, and a follow-up that is only a proposal](docs/history/research_state_log.md#4z-v5-e32-and-a-follow-up-that-is-only-a-proposal) |  |
| §4aa | [V6-E01: the expansion rule could not reach the reserve, and what a probe would have to absorb (2026-08-25)](docs/history/research_state_log.md#4aa-v6-e01-the-expansion-rule-could-not-reach-the-reserve-and-what-a-probe-would-have-to-absorb-2026-08-25) | 2026-08-25 |
| §4ab | [V6-E02, and a v6 implementation that cannot run (2026-08-25)](docs/history/research_state_log.md#4ab-v6-e02-and-a-v6-implementation-that-cannot-run-2026-08-25) | 2026-08-25 |
| §4ac | [V6-E03: the probe could move the operating point and nothing after it could follow (2026-08-25)](docs/history/research_state_log.md#4ac-v6-e03-the-probe-could-move-the-operating-point-and-nothing-after-it-could-follow-2026-08-25) | 2026-08-25 |
| §4ad | [V6-E04: development asked an easier question, and two bases were never compared on the same cases (2026-08-25)](docs/history/research_state_log.md#4ad-v6-e04-development-asked-an-easier-question-and-two-bases-were-never-compared-on-the-same-cases-2026-08-25) | 2026-08-25 |
| §4ae | [The probe protected one slot, and its margin was absorbing sampling noise (2026-08-25)](docs/history/research_state_log.md#4ae-the-probe-protected-one-slot-and-its-margin-was-absorbing-sampling-noise-2026-08-25) | 2026-08-25 |
| §4af | [The v6 decision set was audited, and two of its entries did not mean what they said (2026-08-26)](docs/history/research_state_log.md#4af-the-v6-decision-set-was-audited-and-two-of-its-entries-did-not-mean-what-they-said-2026-08-26) | 2026-08-26 |
| §4ag | [m\* is frozen at Gate 2, the decisions are closed, and v6 is adopted (2026-08-26)](docs/history/research_state_log.md#4ag-m-is-frozen-at-gate-2-the-decisions-are-closed-and-v6-is-adopted-2026-08-26) | 2026-08-26 |
| §4ah | [Stage 1 could refuse a study once and end a replication (2026-08-26)](docs/history/research_state_log.md#4ah-stage-1-could-refuse-a-study-once-and-end-a-replication-2026-08-26) | 2026-08-26 |
| §4ai | [§12.6 had no rule for a rung with no difficulty coordinate (2026-08-26)](docs/history/research_state_log.md#4ai-126-had-no-rule-for-a-rung-with-no-difficulty-coordinate-2026-08-26) | 2026-08-26 |
| §4aj | [A probe stand-in had no admissible severity, and ended the stage (2026-08-27)](docs/history/research_state_log.md#4aj-a-probe-stand-in-had-no-admissible-severity-and-ended-the-stage-2026-08-27) | 2026-08-27 |
| §4ak | [v6 closed with zero survivors, and v7 withdraws the composed-headroom criterion (2026-08-27)](docs/history/research_state_log.md#4ak-v6-closed-with-zero-survivors-and-v7-withdraws-the-composed-headroom-criterion-2026-08-27) | 2026-08-27 |
| §4al | [The v7 boundary machinery audited statistically; the structural-zero veto withdrawn (2026-08-28)](docs/history/research_state_log.md#4al-the-v7-boundary-machinery-audited-statistically-the-structural-zero-veto-withdrawn-2026-08-28) | 2026-08-28 |
| §4am | [v7 adopted, registered, and executed as the prospective confirmatory study (2026-08-28)](docs/history/research_state_log.md#4am-v7-adopted-registered-and-executed-as-the-prospective-confirmatory-study-2026-08-28) | 2026-08-28 |
| §4an | [v7 amended in place after the closure: D6 reaches the freeze, C4 gates the spectrum (2026-08-28)](docs/history/research_state_log.md#4an-v7-amended-in-place-after-the-closure-d6-reaches-the-freeze-c4-gates-the-spectrum-2026-08-28) | 2026-08-28 |
| §4ao | [The §13.11 chance column had been zero on every replication; corrected on the Gate-2 producer, outside §13's pin (2026-08-29)](docs/history/research_state_log.md#4ao-the-1311-chance-column-had-been-zero-on-every-replication-corrected-on-the-gate-2-producer-outside-13s-pin-2026-08-29) | 2026-08-29 |
| §4ao | [Development-only diagnosis of the v7 difficulty spectrum: C4's causes, and a wording-parse artefact inside the exact-count instrument (2026-08-29)](docs/history/research_state_log.md#4ao-development-only-diagnosis-of-the-v7-difficulty-spectrum-c4s-causes-and-a-wording-parse-artefact-inside-the-exact-count-instrument-2026-08-29) | 2026-08-29 |

## 5. Provisional, superseded, broken, unresolved

- **Superseded.** The capped reasoning-curve exports under
  `exploratory/figures/reasoning_compute/data/` were built by a figure path that
  bypassed the canonical-evidence guard. Marked, retained, not regenerable in this
  checkout — `PROVENANCE.json` there says exactly what and why. The natural-endpoint
  headline is unaffected.
- **Void.** The anti-splice intervention failed its own manipulation check
  (`ANTI_SPLICE_MANIPULATION_FAILED`). A failed manipulation check voids an
  estimate; it does not weaken it into a null.
- **Closed, and preserved.** DCI-1 v4r3 is terminal at `GATE_1_MEASUREMENT`
  with `MEASUREMENT_EVIDENCE_INSUFFICIENT`. Its registered criterion asked
  whether external reviewers reproduce the verifier and neither pathway
  established that; the later §10.7-R5 amendment then blocked on a `CP4`/`CP7`
  wording. Both records stand, neither pathway is described as having
  succeeded, and nothing under v4r3's source, test, evidence, durable or report
  trees was edited to reach v4r4. `dci1/reports/dci1v4r3/closure.json`. §4l,
  §4m.
- **Superseded, and preserved.** The earlier `GATE_1_BLOCKED_MEASUREMENT`
  decision was correct under the rule then in force — §10.2 plus §10.3 or
  §10.4, neither of which completed. §10.7-R5 changed the rule, not that
  record, and v4r4 changes it again prospectively; neither describes either
  pathway as having succeeded. §4k, §4l, §4m.
- **Limiting, for v4r4 (since superseded).** Under v4r4, §12.6's C4 is met on
  all four models but with **no leave-one-family-out margin on three of them** — exactly four
  well-formed straddling feature groups, every one load-bearing. Inherited from
  v4r3's reference pool, not created by removing `CP4`/`CP7`. The registered
  expansion is deliberately not invoked (`DECISIONS_V4R4.md` B7), so any
  Gate-3 or Gate-4 result on those three models is conditional on all four
  groups holding. §4m.
- **Unanswered, permanently scoped.** v4r4's measurement basis is
  `deterministic_measurement_validated`, never `human_validated`. §10.5's scope
  sentence therefore attaches to every analysis record: the outcomes are
  verifier-defined and support no claim about compliance as an independent
  human would judge it. §4m.
- **Blocked.** The five-checkpoint vLLM TP=2 qualification gate passed 0/5, for
  three unrelated reasons (`ROOT_CAUSE_ANALYSIS.md`). The Transformers-vs-vLLM
  backend confound on the transport question is therefore unresolved.
- **Withdrawn.** Several early quantitative claims — a nested correlation, a
  mislabelled statistic, a buggy sentence counter, a shared-seed replicate regime.
  Kept and marked in section D of `CLAIM_EVIDENCE_MATRIX.md`; never cited as support.
- **Known, and deliberately deferred (v7 only).** v7's `StudyContext`
  (`dci1/src/dci1v7/engine/context.py`) refuses another study's tree only when
  that tree exists on disk. In a fresh clone, then, a v7 synthetic or
  development root under a directory named for another study (for example
  `…/dci1v6/nested`) is accepted. Where the foreign tree is present the overlap
  check still refuses it, and a stage record carrying another study's
  `study_id` is still refused (`engine/transitions.py`). The fix refuses a
  foreign name on every path component and names the historical trees without
  listing the disk. It exists as `d163232` on the tag
  `archive/maint/v7-docs-marker-unification` and is not on `main`. It is
  deferred rather than applied for three reasons. v7 is closed. Its
  registration binds producing commit `ed0446f`, so any re-run needs a §32
  superseding registration, which is where this fix belongs. And no active
  code uses the module: v8.1 has its own context, which checks every ancestor.
  Raised by the Codex review of PR #31. CI shows it: `tests_v7`'s
  `test_v5_cannot_adopt_a_v4r4_evidence_root` is a strict expected failure
  wherever `dci1/evidence/dci1v4r4` is absent, and fails the run if the refusal
  ever starts working without that tree. `tests_v5` and `tests_v6` carry the
  same test and, since 2026-10-18, the same marker.
- **Known broken, and deferred: four pinned paths in v6 and v7.** `dci1v6` and
  `dci1v7` were derived from `dci1v5` with the revision renamed throughout, and
  the rename carried two decision-packet paths with it: their manifests and
  verifier modules cite `dci1/reports/dci1v{6,7}/d4_marker_audit.md` and
  `…/u2_tier_model_decision.md`, which never existed. The packets were
  committed only under `dci1/reports/dci1v5/` (`6760c2b`), and that is what the
  citations refer to. Not repaired, for the reason above: both studies are
  closed and the strings are registered code.
  `dci1/tests_v8dev/test_pinned_document_paths.py` lists exactly these four as
  known broken and fails if any other pinned document goes missing.
- **Not reproducible from a clone.** `runs/` is gitignored and absent. The run
  manifests hash files a fresh checkout does not have. See
  `exploratory/evidence/README.md` for the promotion path that fixes this per claim.
- **Resolved, and the ground is on the record.** §12.6's eligibility
  predicate — open item **U4**, which blocked the v5 registration — is
  closed at **E2**: a rung is eligible when $p_{\text{solo}}(R) \in
  [0.10, 0.90]$ with the registered vacuity ceiling. §13.4 bands
  $p_{\text{solo}}$ and bands $\iota$ nowhere, so the alternative would
  have invented an absolute threshold on $\iota$. The coverage criterion
  is unchanged and still positions rungs by $\iota$. §4x.
- **Registered, not licensing anything.** §18 step 14's raw-coordinate
  replication of the §11.8 fit is computed, and step 12's simultaneous
  interval is recorded `NOT_REGISTERED_FOR_INFERENCE`: §15 gives the
  replication marginal intervals only and declares no family containing a
  raw-coordinate member. Its one consequence is §17.6's
  `DIFFICULTY_COORDINATE_DEPENDENT`. §4x.
- **Retained, and not reusable.** Every behavioural row produced under a
  *superseded* v5 registration — 478,464, under six of them —
  is preserved under `superseded/` and invalidated. Each was produced under
  a screen whose coverage criterion evaluated an empty set, whose
  $\iota_A$ came from the wrong severity, whose §7.2 escalation refused on
  its first instruction, and whose expansion could not run. The live
  evidence path under `af5fa4bc…` holds none of them, and no restarted stage
  can resume into them. Separately, the 459,312 rows produced under
  `af5fa4bc…` itself are live but **pre-confirmatory**: gate and development
  evidence only, supporting no claim about the effect. §4w, §4x, §4y.
- **Open, and most valuable next:** the boundary-affordance causal crossing; a
  pair with a genuine trade-off region; finishing the cross-model dataset on one
  backend.

## 6. Recent consequential changes

[`CHANGES_SCIENTIFIC.md`](CHANGES_SCIENTIFIC.md) — measurement-affecting changes
only, newest first, each stating what changed, which results are affected, and
whether old and new remain comparable. Most recent, all 2026-09-13: three v19
review fixes (the verifier hash closure, the Stage 2 report's bundle identity,
and stage gates that reach upstream stages), the v19 Pair 3
sentence-segmentation repair ported to main from PR #22, a post-confirmatory
audit that found two gaps in the frozen v8.1 analysis that did not affect the
executed run, and exploratory fixes to the arbitration summaries, the
cross-model verdict column and the natural-reasoning robustness figure. Before
them: the v8.1 confirmatory analysis, executed once on 2026-09-10, and the v8
and v8.1 design changes of 2026-08-29 to 2026-09-03, summarised in §4d. Before
those: §13.11's chance column,
zero on every replication of v5–v7, corrected on the Gate-2 producer to
§13.2's unconstrained-cell κ_c with degenerate candidates withheld and
recorded; no pinned §13 module and no threshold changes; stored tables are
not comparable with corrected ones and no record is re-verdicted — in §4ao.
Before it: v7 amended in place
after its closure (A6–A8, 2026-08-28) — the pre-freeze `support_satisfied`
check withdrawn for the registered invariant so a D6 non-identified
replication reaches the freeze, §12.6's C2/C4 scoped to the spectrum arm and
C1/C3/C5/C6 to the core arm with no value moving, D6's meaning stated once —
in §4an. Before it: v7 adopted, registered
and run on 2026-08-28, and closed with zero survivors of four — every
replication passed the stages v7 changed and every one lost `Delta_R` at
Gate 3C on §12.6's C4 under the calibrated re-read, then ended on the
pre-freeze audit's `support_satisfied` check — in §4am. Before it: v7's §13.14 boundary
machinery audited on the production interval procedure (39,000 simulated
experiments) — the Wilson allowance kept as necessary, the structural-zero
veto withdrawn as V10, Gate 4 shown non-adaptive, the sign convention
verified — in §4al. Before it: v6 closed with zero
survivors of four — both Qwens on B's compliance rising under A toward the
ceiling, one Gemma on a companion's own solo cell, one at the pre-freeze audit
on a document hash the lifecycle could not amend — and v7 drafted: the
absolute composed-headroom criterion withdrawn as a terminal requirement and
replaced by readings of the contrast (structural zero, arm at a boundary,
compressed direction), Gate 2.75 and Gate 4 recording the paired contrasts by
the confirmatory estimators, and a bindable post-registration amendment; no
threshold moves and the estimand layer is byte-identical — in §4ak. Before it: v6's amendment A17 — the first composed probe refused because a probe-only stand-in had no severity inside its placement band; it is now recorded as STANDIN_UNPLACEABLE and the cells it carries as NOT_MEASURED_STANDIN_UNPLACEABLE, entering no verdict, which is the set that never entered one anyway — in §4aj. Before it: A16 — §12.6 had no rule for an eligible rung whose difficulty coordinate is undefined and the first live REGIME_SCREEN died on one; such a rung is now dropped from every coverage condition and recorded, a direction that can only make the conditions harder to meet, declared under §32.2 as adopted after the observation — in §4ai. Before it: A15 — a §18 stage-1 readiness verdict is a refusal, not a §28 terminal outcome, so a blocker naming outstanding researcher work no longer ends the replication that discovers it; the criterion is unchanged, every §28 terminal outcome is untouched, and the one record an apparatus fault wrote is retained and hash-bound — in §4ah. Before it: m\* frozen at Gate 2, §34 D23 = `projection_sd` and D26 = 0.0142, and v6 adopted — in §4ag. Before it: v6's Gate-2.75 widened from
one slot to all ten of §13.14's exposure classes and its margin constant
replaced by a per-entry projected interval, three `probe_only` stand-ins
authored, and §13.14's precision left as registered because the enlargement it
was to get is not executable here — in §4ae. Before it: V6-E04 — v6's development
prescreen evaluated a proxy for §13.15 rather than §13.15, and §12.6 was
certified on one sample and re-read against another; one implementation of the
criterion now serves the stages, the search and the pilot, the coverage
re-reading is paired and gates, and the probe stopped re-measuring cells Gate 2
already had — in §4ad; and V6-E05, a summary count on every Gate-3A record that
read a key §13.7 never returns, so `n_stable` was 0 on all four signed v5
replications beside 9 to 16 candidates that passed. Before it: V6-E03 — v6's composed
probe could move the operating point and no stage after it could follow, so the
re-selection branch that is v6's whole answer to v5's Gate-4 failure ended in
an unhandled error; repaired, with a scenario that drives it to the freeze, and
with the estimand layer now checked file by file against v5 — in §4ac. Before
it: the v6 implementation, which cannot run — the V6-E01 and V6-E02 expansion
repairs, a nineteenth stage, and no threshold moved — in §4ab. Before it: V6-E01 — §12.6's expansion
could not reach the Tier-1 reserve §7.10 widened for C4's span, which narrows
the v5 survival diagnosis without changing a v5 verdict — in §4aa. Before it:
v5 closed with no replication reaching confirmatory generation, and V5-E32, a
registered terminal status with no raise path — in §4y and §4z. Before it:
v5's §12.6 eligibility predicate resolved at E2 and §18 step 14's
raw-coordinate fit implemented as §15 registers it, with one clean superseding
registration and all four replications qualified — in §4x. Before it: the v5 stage 3–18
execution-path audit — twelve registered rules that the production path did
not execute, and one, §12.6's eligibility predicate, that the preregistration
did not determine — in §4w. Before it: DCI-1 v5 drafted — the core
reference pool inverts to production class and same-form with A, a
pre-composition interaction gate is added, and two v4r4 documentation values
are corrected without moving a number — in §4q. Before it: the whole pipeline
below Gate 1 executed for the first time and nineteen defects, most of one
class — a reader with no producer — moved what a v4r4 record says, in §4n, §4o
and §4p.

## 7. Where to look

| To see | Go to |
|---|---|
| what each experiment family did | `exploratory/EXPERIMENTS.md` |
| the claim ledger with evidence | `exploratory/CLAIM_EVIDENCE_MATRIX.md` |
| why an experiment was chosen | `exploratory/DECISIONS.md` (written before each run) |
| what the metrics mean exactly | `exploratory/METRIC_SPEC.md` |
| which data files are admissible | `exploratory/REASONING_DATA_PROVENANCE.md` |
| what was actually covered | `exploratory/EXPERIMENT_COVERAGE_MATRIX.md` (rebuilt from run configs) |
| the v19 confirmatory protocol (a separate study, paused) | `README.md`, `docs/MIGRATION.md`, `docs/preregistration/` |
| the frozen Stage 2 decisions | `src/dci/v19/stage2_frozen.json`, `docs/v19_stage2_specification_amendments.md` |
| the current DCI-1 protocol (v8.1), its result and the manuscript rewrite map | `dci1/docs/DCI1_preregistration_v8.1.md`, `manuscript/V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md`, `manuscript/POSTCONFIRM_EXEC_SUMMARY.md`, `dci1/reports/dci1v8dev/postconfirm/` |
| the v4r4 protocol (superseded) | `user-notes/DCI1_preregistration_v4r4.md` (incorporates v4r3's by reference) |
| the v5 protocol (run and closed) | `user-notes/DCI1_preregistration_v5.md` (standalone), `user-notes/DCI1_v4r4_to_v5_changelog.md` |
| why v5 exists, measured | `dci1/reports/dci1v5/reference_design_development.md`, `dci1/reports/dci1v5/reference_design_spec.json` |
| what v5 adopted, item by item, and what comes next | `dci1/reports/dci1v5/v5_adoption_checklist.md` |
| why v7 exists, and the statistical argument for estimating the contrast rather than gating the arms | `dci1/reports/dci1v7/READINESS.md`, `user-notes/DCI1_preregistration_v7.md` |
| whether v7's boundary rule is statistically valid, measured on the production procedure | `dci1/reports/dci1v7/boundary_audit/DECISION_MEMO.md`, `dci1/tools/v7_boundary_audit.py` |
| the v7 implementation and its executable change list | `dci1/src/dci1v7/protocol/revision.py`, `dci1/src/dci1v7/analysis/boundary.py`, `dci1/tests_v7/` |
| what the §13.11 chance column's correction moves on every stored calibration table, per model | `dci1/reports/dci1v7/chance_basis_impact/REPORT.md`, `dci1/tools/v7_chance_basis_impact.py` |
| which development rehearsals ran on the zero chance column, and how to start one on the corrected tree | `dci1/reports/dci1v7/development_rehearsal/README.md` |
| every v7 §34 closure, its value, its evidence, who took it and where it was carried from | `dci1/reports/dci1v7/researcher_decisions.json` |
| how v7 was run, replication by replication, and how it closed | `dci1/tools/run_v7_replication.sh`, `dci1/reports/dci1v7/execution_logs/`, `dci1/reports/dci1v7/closure.json` |
| how v6 closed, replication by replication | `dci1/reports/dci1v6/CLOSURE.md`, `dci1/reports/dci1v6/closure.json`, `dci1/reports/dci1v6/incidents/` |
| what v6 would have to fix, and what is still the researcher's | `dci1/reports/dci1v6/READINESS.md`, `dci1/reports/dci1v6/readiness_evidence.json` |
| the v6 implementation, and why it cannot run | `dci1/src/dci1v6/protocol/revision.py`, `dci1/src/dci1v6/protocol/decisions.py`, `dci1/tests_v6/` |
| how precise Gate 4 is, and what a margin has to absorb | `dci1/tools/v6_precision_design.py`, `dci1/reports/dci1v6/precision_design.json` |
| the two expansion defects, replayed side by side | `dci1/tools/v6_expansion_dryrun.py`, `dci1/reports/dci1v6/expansion_dryrun.json` |
| what remains a limitation rather than a decision | `dci1/reports/dci1v5/v5_prereg_redteam.md` (R5 above all), `dci1/reports/dci1v5/v5_implementation_status.md` §4 |
| every §34 closure, its value, its evidence and who took it | `dci1/reports/dci1v5/researcher_decisions.json` — including D17's floor spec and U2's and P1's resolutions |
| the four decision packets, as adopted | `dci1/reports/dci1v5/d1_arm_compute_decision.md`, `d4_marker_audit.md`, `d17_b_strength_decision.md`, `u2_tier_model_decision.md` |
| every v5 field, its producer and its readers | `dci1/reports/dci1v5/v5_producer_consumer.md` |
| what v5's implementation is, and what it cannot do | `dci1/src/dci1v5/`, `dci1/tests_v5/`, `dci1/reports/dci1v5/v5_implementation_status.md` |
| every v5 document discrepancy and its classification | `dci1/reports/dci1v5/v5_reconciliation.md` |
| what v4r4 changed and why | `user-notes/DCI1_v4r3_to_v4r4_changelog.md` (R4-1–R4-7) |
| the v4r4 decisions register | `dci1/DECISIONS_V4R4.md` (B0–B7, E0–E7) |
| what v4r4 measured, and its follow-up | `dci1/reports/dci1v4r4/` — `final_results.json`, `EXECUTION_REPORT.md`, `SCIENTIFIC_FOLLOWUP_EVIDENCE.md` |
| why v4r3 stopped, and what it left | `dci1/reports/dci1v4r3/closure.json`, `dci1/reports/dci1v4r3/REPORT.md` |
| the superseded v4r3 protocol and register | `user-notes/DCI1_preregistration_v4r3.md`, `dci1/DECISIONS_V4R3.md` |
| the v4r3 implementation, preserved | `dci1/src/dci1v4r3/README.md` |

## 8. Keeping this file honest

It is derivative by design: claims link to reports, reports link to runs, runs
carry their own configuration. Update §4–§6 when `CHANGES_SCIENTIFIC.md` gains an
entry; if a statement here cannot be traced to a linked artifact, delete it rather
than maintain it.
