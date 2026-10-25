# Batch 1 remediation after the independent audit and the re-audit

This report has two rounds. §1–§11 are the first round (audit findings
F1–F10), kept as written. **§R is the second round** (re-audit findings
R1–R4 and the researcher's instructions of 2026-10-19), and its verdict is the
current one. The researcher-facing review package starts at
[`RESEARCHER_REVIEW.md`](RESEARCHER_REVIEW.md).

- **Audit:** `../audit-batch1-2026-10-19/AUDIT_REPORT.md`, dated 2026-10-19. Its verdict was *approvable after specific fixes*.
- **Probes:** `../audit-batch1-2026-10-19/probes/`.
- **Repository:** `cnm13ryan/dci`.
- **Branch:** `feat/batch1-pilot-calibration`.
- **Base:** `main` = `0d85a8e`.
- **State:** uncommitted (§2).

Nothing here ran a model:
- no GPU job, pilot generation or composed outcome;
- no decision was approved;
- no freeze was made from synthetic evidence;
- no historical file was touched.

## 1. Findings, actions and status

Every audit counterexample was reproduced before it was fixed (§4). Each is now
a permanent regression test.

| Finding | Action | Files changed | Tests | Status |
|---|---|---|---|---|
| **F1** (P1) Empty answers left the denominators; failed backend rows were reused forever | Every backend row is now classified VALID, EMPTY or TECHNICAL. **Empty answers:** a completed blank answer (the seam's `CHANNEL_INVALID` under NO_THINKING, when the row shows it) is EMPTY: in n, never compliant, not regenerated. **Technical rows:** they never enter `rows.jsonl`. They go to `rejected.jsonl` with their attempt number and are retried on resume. **Blocked engine:** an exit code 2, or a blocked, missing or unreadable sidecar, is refused outright. **Crash:** an exit code 3 keeps the complete rows and refuses the rest. **Other safeguards:** a run lock; identical duplicates collapse and conflicting ones refuse; a partial last line is repaired and recorded; seeds and identities are checked on receipt. This carries v8.1's `reusable_rows_checked` rule (blocked sidecar → regenerate) and extends it to per-row outcomes. | `outcomes.py` (new), `store.py` (new), `runner.py`, `scoring.py`, `verifiers.py`, `synthetic.py` | `test_outcomes_and_runner.py`: 31 tests, including the 8 required regressions and audit probe E through a real subprocess stub | Fixed |
| **F2** (P1) Stage 2 could be planned and run from an incomplete Stage 1 | A completeness gate: every frozen design row needs exactly one accepted generation and one score derived from it, under the current verifier bundle, with nothing open. **Selection:** it is re-scored before it is computed, and it records the Stage 1 evidence hash. **Stage 2:** planning, execution and finalisation recompute that hash and refuse a mismatch. **Finalisation and Freeze 2:** both need both stages complete. There is no partial-completion rule. | `evidence.py` (new), `pipeline.py`, `cli.py` (`status`, exit code 4) | `test_stage_gates.py`: a one-third Stage 1 cannot plan Stage 2 (audit probe F); an edited or stale Stage 1 response or score is caught; Stage 2 resumes without moving the selection; an interrupted Stage 2 cannot finalise | Fixed |
| **F3** (P1, decision D08) A floor-level A could be selected and reported FEASIBLE | D08 revised: an N is admissible only if p_A is in [0.10, 0.90] in at least 6 of 8 model-frames, across at least 3 models. A configuration with an uninformative A is reported but never counted toward feasibility. If no admissible N exists, selection FAILS. There is no per-model fallback. The thresholds are proposed defaults in the configuration. | `calibration.py`, `references.py`, `config.py`, `report.py` | `test_selection_revisions.py`: the audit's floor surface, verbatim, plus 3% everywhere, 97% everywhere, moderate, partly informative, better coverage with worse headroom, uninformative configurations reported but not counted, and inclusive band edges | Fixed; **awaiting approval** |
| **F4** (P1) Topic overlap ignored the v2/v3 banks | The check now reads every historical DCI bank in the repository: 2,096 questions and 192 sequestered hashes. **The screen:** word-set Jaccard ≥ 0.5 or stemmed content-word Jaccard ≥ 0.3, with every flagged pair needing a recorded decision bound to both texts. **Rewrites:** 42 questions were rewritten under their ids, so the split is unchanged: 36 reuses (5 pilot, 31 reserved) and 6 library-word leaks. 37 pairs were kept as distinct, with rationales. **Hygiene report:** question form, instruction-like content, library words, and Stage 1 / Stage 2 / reserved profiles. | `topics.py`, `data/topics_source.json`, `data/topics_review.json` (new), `report.py` | `test_topics.py`: the 4 audit examples are detected; every replaced question would be flagged; revisions do not move the split; a review decision is bound to its text; hygiene detection | Fixed; **bank awaits researcher review** |
| **F5** (P2, raised to P1) `execute` did not authenticate the design file | Before any backend starts, every requested row is compared field by field with the design regenerated from Freeze 1 (and, for Stage 2, from a selection recomputed from complete Stage 1 evidence). **Recomputed from scratch:** prompt hash from the prompt bytes, seed, identity, and instruction count. **Refused:** a repeated row id or a row outside the design. The same check runs for resume and for scoring. | `evidence.py`, `runner.py`, `design.py` (`design_digest`, `instruction_lines`) | `test_stage_gates.py`: the audit's attack (a second instruction with `load: 0`) is refused before the backend, as are an altered seed, an edited topic or topic id, a duplicated row, a changed frame, an edited prompt with a recomputed hash, a forged plan (the prompt-byte instruction count), a stale Stage 2 plan, and a tampered plan file through the CLI | Fixed |
| **F6** (P2) Membership and feasibility are unstable under pilot noise | A simulation study through the real selection code: 6 surfaces × 7 allocations × 100 pilots, with topic random effects. **D14 (new, proposed):** a topic-cluster bootstrap reporting inclusion frequency, the A, B and FEASIBLE shares, borderline matches, a Stage-1-only sensitivity, and feasibility on majority-stable members. It is bound in Freeze 2, and is a diagnostic, not a gate: in simulation it does not reliably separate true from false FEASIBLE verdicts. **Allocation:** no change recommended (see the precision review). | `stability.py` (new), `simulate.py` (new), `freeze.py`, `pipeline.py` | `test_smoke_and_stability.py` (topic clustering, determinism, diagnostic-only); `test_end_to_end.py` (bound in Freeze 2) | Characterised; D14 awaits approval as a diagnostic (simulation shows it is not a reliable gate) |
| **F7** (P2) Approvals bound parameters, not rules; configuration and environment were unbound | Each decision payload binds code hashes of its implementing modules. The hashes exclude docstrings and comments, so a documentation edit voids nothing. D02 binds the frames and templates; D12 binds the configured models, seeds and the vLLM seam source; D05 binds the topic bank and split. **Freeze 1:** it binds every executing module (including `pipeline.py`), `rules.py`, `hashes.py`, the seam source, and an environment lock. The lock is attested on the generation host (`attest-environment`), never fabricated, and re-probed live at `execute`. | `config.py`, `freeze.py`, `store.py` (`code_hash`), `environment.py` (new), `cli.py` | `test_integrity.py`: 19 tests (selection code voids exactly D06–D08; reference code voids D08–D11 and D13; a documentation edit voids nothing; config fields reach their decisions; the template binds D02 and the design; an edited seam voids D12 and blocks the lock; live environment mismatches refuse); `test_freeze.py` | Fixed |
| **F8** (P2) Freeze 2 did not bind response text or scores | Freeze 2 binds per-stage design digests, hashes of every accepted response record and every full score vector, the outcome classes, the separate technical-attempt log, the Stage 2 selection and the evidence it read, the tables, the calibration and D14. `validate-freeze` rebuilds it all and re-scores every response. | `freeze.py`, `pipeline.py`, `scoring.py` (`generation_hash`), `evidence.py` | `test_end_to_end.py`: an edited response (before and after re-scoring), a flipped verdict, a duplicated row and an edited manifest are each detected; synthetic evidence cannot be frozen | Fixed |
| **F9** (P2, decision D07) B could select near-identical limits | D07 revised: a pair needs median separation of at least 0.15, that separation in at least 3 models, and each limit informative in at least 4 of 8 model-frames. If no pair qualifies, selection FAILS. Ties go to the smaller limits. The threshold was checked by simulation (§7 of the precision review). | `calibration.py`, `config.py`, `report.py` | `test_selection_revisions.py`: the audit's plateau, verbatim, plus nearly identical limits, clear separation, one- or two-model separation, a floor or ceiling limit, ties, the inclusive and configurable threshold, and failure that is never FEASIBLE | Fixed; **awaiting approval** |
| **F10** (P3) Smaller issues | **Duplicates:** collapse when identical, refuse when conflicting; scoring twice refuses. **Truncated passes:** no longer counted as vacuous; literal, vacuous, truncated and empty passes are counted separately. **Smoke test:** a bounded, authorised `smoke` command (≤ 96 rows, its own namespace, no compliance computed). **Stage-1-only sensitivity:** in calibration and Freeze 2. **Topic profiles:** compared by stage. **Diagnostics:** `structure_lines` (markdown structure) and `refusal_like`. **D12:** a truncation-review share. **Changelog:** the `2026-09-13` heading in `CHANGES_SCIENTIFIC.md` is restored. **Disclosures:** D09, D10, D11 and D13. | `store.py`, `scoring.py`, `verifiers.py`, `smoke.py` (new), `stability.py`, `topics.py`, `calibration.py`, `CHANGES_SCIENTIFIC.md` | `test_outcomes_and_runner.py`, `test_smoke_and_stability.py`, `test_verifiers.py` | Fixed |
| §11 Joint compatibility under the 60–120-word contract | A second, independent witness construction (`LONG_POOL`, deterministic per family). All 305 compatible cells have a 64–93-word witness that complies under X and B. The logical matrix is unchanged at 305 / 19 / 0. | `compatibility.py`, `report.py` | `test_compatibility.py` | Done: 305 of 305 |

## 2. Branch and working tree

- **Branch:** `feat/batch1-pilot-calibration`, from `main` `0d85a8e`.
- **Commits:** none. Nothing was committed, stashed, reset or overwritten.
- **Untracked (new):** `src/dci/batch1/`, `tests/batch1/`, `docs/batch1/`.
- **Modified:** `CHANGES_SCIENTIFIC.md`, `README.md`, `RESEARCH_STATE.md`.

Nothing changed under `dci1/`, `configs/`, `exploratory/` or elsewhere in
`src/`. `test_historical_v81_sources_are_unchanged_since_the_freeze` checks
the v8.1 sources.

## 3. Files created or modified in this remediation

**New modules:**

| module | role |
|---|---|
| `store.py` | strict JSONL, canonical hashes, the duplicate policy, the run lock, code hashes |
| `outcomes.py` | the VALID / EMPTY / TECHNICAL classes |
| `evidence.py` | design authentication, the completeness gate, the selection binding |
| `environment.py` | probe and lock |
| `stability.py` | D14 |
| `smoke.py` | the bounded smoke test |
| `simulate.py` | the precision study |

**Changed modules:** `runner.py`, `pipeline.py`, `freeze.py`, `config.py`,
`calibration.py`, `references.py`, `scoring.py`, `verifiers.py`, `design.py`,
`topics.py`, `compatibility.py`, `synthetic.py`, `report.py` and `cli.py`.

**Data:**
- `data/topics_source.json`: 42 questions revised; a `revisions` record added;
- `data/topics_review.json` (new).

**Tests:**
- **new:** `helpers.py`, `test_outcomes_and_runner.py`, `test_stage_gates.py`,
  `test_selection_revisions.py`, `test_integrity.py`,
  `test_smoke_and_stability.py`;
- **rewritten:** `test_end_to_end.py`;
- **updated:** `test_freeze.py`, `test_topics.py`, `test_selection.py`,
  `test_compatibility.py`, `test_review_artifacts.py`.

**Docs:**
- **new:** this report, `CALIBRATION_PRECISION_REVIEW.md`,
  `calibration_precision.json`, `topic_review.md` (renamed `topic_screen_report.md` in the second round), `topic_hygiene.json`;
- **updated:** `README.md`, plus every generated artifact (regenerated);
- **outside `docs/batch1`:** `CHANGES_SCIENTIFIC.md` (a new entry, and the
  restored heading), `RESEARCH_STATE.md` and `README.md` (pointers).

## 4. Reproducing the audit before fixing

All counterexamples reproduced on the pre-remediation tree:

| probe | before the fix |
|---|---|
| C | a second instruction with `load: 0` was sent to the generator |
| D | an empty `CHANNEL_INVALID` B row gave `k=0, n=0, non_behavioural=1` |
| E | 40 blocked rows were "generated, no exception", then "0 generated, 40 reused" |
| F | 5,205 of 15,616 Stage 1 rows produced a 150-cell, 9,600-row Stage 2 plan |
| G | 180 of 240 refined cells became unusable |
| §4 | A.however.6 at p_A = 0.03 was selected, FEASIBLE |
| §5 | B (8, 10) was selected at medians 0.16 and 0.17 |

The extended overlap scan found the four audit examples, and 32 more
same-phenomenon restatements in v2, v3 and v19.

**After the fixes**, the auditor's scripts were rerun:

| probe | result |
|---|---|
| A | every gate refusal still holds |
| B | no configuration field is outside a payload |
| C | `DesignAuthenticationError` before the backend |
| D | refused as TECHNICAL. The probe's hand-built row has no raw text or finish reason, so nothing shows a completed generation. The seam's real row (`raw_generation`, `finish_reason`) is classified EMPTY and counts in n, as tested in `test_a_successful_empty_answer_is_in_the_denominator_and_fails`. |
| E (verbatim) | "blocked (exit 2; CAPACITY_EXCEEDED); 40 rows rejected, none accepted", twice; nothing stored as evidence |
| F | `IncompleteEvidence` |
| G | finalisation refuses an incomplete Stage 2 |
| `probe_selection` §4 | A.however.2 is selected, `INFEASIBLE_REVISION_REQUIRED`, `A_COVERAGE_INADEQUATE`; A.however.6 is inadmissible |
| `probe_selection` §5 | B `FAILED`; no pair selected |

## 5. Tests

**Results, 2026-10-19, macOS, CI's marker filters:**

| suite | command | result |
|---|---|---|
| Batch 1, CPU tier | `pytest tests/batch1 -m "not slow and not gpu and not rocm and not cuda and not cloud"` | **537 passed**, 0 failed (7 min 18 s; it was 422 before the remediation) |
| Batch 1, slow (full-size synthetic demo, 20 stability resamples) | `pytest tests/batch1 -m slow` | **1 passed** (5 min) |
| root `tests/` (includes Batch 1) | `pytest tests -m "not slow and not gpu and not rocm and not cuda and not cloud"` | **3,259 passed**, 0 failed (it was 3,144) |
| `exploratory/tests` | `pytest exploratory/tests` | 637 passed, **6 failed** (`test_runlock_ownership.py`) |
| `dci1/tests_v8dev` (dci1 venv) | `pytest tests_v8dev -m "not slow and not gpu"` | 432 passed, **5 failed and 3 errors** (`test_legacy_prescreen_characterization.py`) |

**Failures that predate this work:**
- The exploratory and DCI-1 failures are byte-for-byte the same test ids as
  in the pre-remediation run.
- Both sets reproduced on a clean `main` worktree before Batch 1 existed
  (README §11 of the first report). The prescreen ones are float differences
  around 1e-5 that depend on the host's BLAS, as CI notes; the run-lock ones
  check process ownership on this machine.
- Neither tree was changed, and neither imports `dci.batch1`.
- The documentation-path tests in `tests_v8dev`, which scan the edited docs,
  pass.

**New regressions:** none.

**Independent re-checks:**
- the auditor's `probe_compat.py`: 0 disagreements on the 324 logical cells;
- the auditor's verifiers applied to the 305 full-length witnesses:
  0 disagreements;
- the auditor's `probe_safety.py` and `probe_selection.py`, rerun: see §4.

## 6. Generation counts

These are unchanged:

- **Stage 1:** 15,616 generations.
- **Stage 2:** at most 15,360.
- **Total:** at most 30,976.

The precision review found no affordable allocation that changes membership
accuracy or the verdict's reliability materially, so the proposed allocation
stands. D05 and D06 still need approval.

## 7. Semantic changes

These are all proposed, and all recorded in `CHANGES_SCIENTIFIC.md`:

| decision | change |
|---|---|
| D04 | EMPTY answers now count in n (before, they silently left it). Technical rows are never evidence. Truncated passes are no longer called vacuous. The primary definition is unchanged. |
| D06 | Stage 2 requires complete Stage 1 evidence and is bound to it. |
| D07 | Separation, consistency and headroom are now requirements, not tie-breakers. |
| D08 | Headroom is a requirement. Uninformative-A configurations do not count toward feasibility. |
| D14 (new) | A diagnostic only; it changes no membership. |

Unchanged:

- eligibility (the 20% OR rule and the separate 10% extension);
- matching (raw ±0.10);
- G1–G6;
- P1–P3;
- the hierarchical weights;
- the 51-candidate library;
- the seven operations;
- the two frames;
- the global A;
- the two global B limits.

## 8. Decisions awaiting approval

All 14 are listed in `decisions.md`. Each one is `PROPOSED`. Every payload hash
changed in this revision, because each now binds code, so a fresh approval
template has been generated; none had been approved before.

- **Revised or new, needing particular attention:**
  - D04 (outcome classes);
  - D06 (completeness);
  - D07 (0.15, 3 models, 4 of 8);
  - D08 (6 of 8, 3 models);
  - D12 (bindings, the 2% truncation review, the smoke-test policy);
  - D14 (a reported diagnostic; how its flags are reviewed before Freeze 2 is accepted).
- **Disclosures added:** D09 (the OR-rule multiplicity), D10 (noisy
  classification), D11 (anti-conservative coverage counts) and D13 (variant
  weighting).

## 9. Blockers that remain (none for the re-audit)

None of these is an implementation defect:

- **Researcher actions:** approving the 14 decisions, and reviewing the topic
  bank and its review decisions.
- **Host actions:** attesting the environment on the generation host and
  running the authorised smoke test there. A CUDA vLLM backend has not been
  built.
- **Accepted, not fixable within the remediation:** the precision review's
  finding that the verdict is unreliable near the 12-of-16 threshold, and
  anti-conservative there. No affordable allocation fixes it, and the D14
  diagnostics do not reliably detect it. Fixing it would mean changing the
  coverage rule (D11) or the matching criterion (D10). Both are scientific
  decisions left to the researcher.

## 10. Commands for a focused re-audit

```bash
cd dci
P=".venv/bin/python"
$P -m pytest tests/batch1 -q -m "not slow"            # Batch 1 CPU tier
$P -m pytest tests/batch1 -q -m slow                  # full-size synthetic demo
$P -m pytest tests -q -m "cpu or not (gpu or slow)"   # root suite, CI markers
$P -m pytest tests/batch1/test_outcomes_and_runner.py tests/batch1/test_stage_gates.py \
    tests/batch1/test_selection_revisions.py tests/batch1/test_integrity.py \
    tests/batch1/test_end_to_end.py -q                # the F1-F9 regressions
$P -m dci.batch1 check-compatibility                  # 305/19/0 and 305 task-level
$P -m dci.batch1 write-review-artifacts --out "$(mktemp -d)"   # compare with docs/batch1
$P -m dci.batch1 demo --root "$(mktemp -d)/demo" --replicates 20
$P -m dci.batch1.simulate --reps 100 --workers 9 --d14-pilots 60 --d14-boot 100 \
    --out "$(mktemp -d)/precision.json"               # reproduces calibration_precision.json
# the auditor's probes, against the remediated tree:
$P ../audit-batch1-2026-10-19/probes/probe_selection.py 20
$P ../audit-batch1-2026-10-19/probes/probe_compat.py
```

`probe_safety.py` stops at its first refusal (section C), which is the fix
working. To see every section, run each one separately, as §4 did.
`probe_topics.py` assumes the old `HISTORICAL_SOURCES` shape, a mapping of
name to path, and needs a one-line change to read the new one, a mapping of
name to `(path, format)`.

## 11. Verdict (first round)

Every audit finding (F1–F10) and the §11 compatibility question has a
targeted fix and a regression test. Every counterexample now fails closed.
The Batch 1 tier, the root suite and the slow demo pass, and there are no new
regressions.

**What remains is for the re-audit and the researcher, not for this
remediation:**
- **14 proposed decisions:** among them the revised D07/D08 thresholds and
  the new D14.
- **The topic bank:** 42 rewritten questions and 37 kept-distinct pairs.
- **The disclosed weakness:** minimum-count coverage near the 12-of-16
  threshold, which no affordable allocation or D14 check fixes.
- **The host:** environment attestation and the smoke test there.

Nothing here approves the protocol or makes it ready to launch.

**READY FOR INDEPENDENT RE-AUDIT**

---

# §R. Second round: the re-audit (R1–R4) and the researcher's instructions

- **Re-audit:** `../audit-batch1-2026-10-19/REAUDIT_REPORT.md` (2026-10-19,
  *approvable after specific fixes*; findings R1–R4).
- **Researcher's instructions (2026-10-19):** rewrite the 11 restatements and
  review the bank for paraphrases (D05); study D11 thoroughly before choosing a
  rule; pin Python 3.11 (D12, approved); bind backend provenance in Freeze 2;
  preserve logs across retries; produce a plain-language review package.
- **Not done, as instructed:** no model or GPU run, no decision marked
  APPROVED, no Freeze 1, nothing committed.

## R.1 Findings, actions and status

| finding | action | files | tests | status |
|---|---|---|---|---|
| **R1** (P2) Pilot and reserved topics restated historical questions in words the lexical screen could not see | **Rewrites:** the 11 named questions. A semantic review read all 576 questions against all 1,472 distinct historical questions (four independent model reviewers, then two more passes on the replacements) and found 49 more restatements, 6 internal duplicate pairs and 87 close cases. 88 questions were rewritten in all, under their ids, so the split is unchanged. **Screens:** a rare-stem screen was added (≥ 2 shared stems of ≥ 4 letters used in ≤ 6 questions). The overlap report is unclean while a recorded restatement remains in the bank. The D05 payload binds the screen settings and both review files. **Balance:** the replacements match the originals' length, longest word, letters b and z, and opening word. | `topics.py`, `data/topics_source.json`, `data/topics_review.json`, `data/topics_semantic_review.json` (new), `config.py` (D05 payload), `report.py`, `cli.py` (`topic_screen_report.md`) | `test_topics.py`: 4 new tests (the 11 would be refused if restored; the rare-stem screen catches popcorn/burst; a recorded restatement left in the bank is unclean; R1 rewrites keep id, area, split and form). Two existing tests' fixtures adjusted (below) | Fixed; **bank awaits researcher review** ([`TOPIC_REVIEW.md`](TOPIC_REVIEW.md)) |
| **R2** (P2) Code hashes, so every approval and Freeze 1, depended on the Python minor version | **Hash:** `store.code_hash` hashes a canonical token stream: comments, docstrings, blank lines and layout removed; f-strings that 3.12+ splits into pieces are rejoined from the source. **Pin:** Python 3.11 (researcher-approved) is recorded in every payload (`orchestrator_python`), the approvals template, and Freeze 1 (`orchestrator`); every CLI command, Freeze 1 creation and validation, and the smoke test refuse another minor version and say why. `.python-version` = 3.11. **Backend:** D12 records Python 3.12 for the vLLM backend (its pinned wheel is cp312). A lock for another version is refused, and Freeze 1 blocks one | `store.py`, `config.py`, `environment.py`, `freeze.py`, `cli.py`, `smoke.py`, `.python-version` | `test_pins_and_provenance.py`: every frozen source and every seam file hash identically under 3.11.12, 3.12.9 and 3.13.12 (subprocess); documentation and layout edits keep the hash, code and string edits change it; 3.12 and 3.13 are refused with the reason; a 3.11 patch release validates; approvals for another Python block; a 3.11 backend cannot be locked or frozen | Fixed |
| **R3** (P1, scientific) D11 coverage produces false FEASIBLE verdicts | **Admission:** verified to keep every qualifying reference; a minimum never caps a population. **Study:** 15 rules × 12 scenarios × 1,000 paired simulated pilots (6 new adversarial scenarios), plus 500 per scenario at a larger budget. It covers noise-free ground truth per rule, a decomposition of noise sources, configuration-level accuracy, membership stability, the effect of weighting, and a near-threshold flag. **Finding:** matching noise drives the false FEASIBLE verdicts, and eligibility contributes nothing. P3k3 (P3 minimum 3) gives the best trade-off; no rule cleans the populations. **The rule in the code is unchanged** (design value 2), pending the researcher's choice | `coverage_study.py` (new; not frozen), `simulate.py` (challenge scenarios), `coverage_simulation.json`, `coverage_simulation_cap480.json`, `figures/` | `test_coverage_rules.py`: 9 tests (G5 equals the full qualifying set, recomputed independently; a fully matched pool is admitted whole; the study's design rule equals the pipeline's; stricter counts never add support; paired evaluation; scenario truths as designed) | **Awaiting the researcher's choice** ([`COVERAGE_SIMULATION_REVIEW.md`](COVERAGE_SIMULATION_REVIEW.md)) |
| **R4.1** Freeze 2 did not bind backend provenance | The runner, not the backend, records each backend run's generator (`vllm_backend` or `stand-in`) and the live environment identity hash. A real root accepts only seam runs under the Freeze 1 lock, and only rows carrying the seam's full schema (`outcomes.SEAM_ROW_KEYS`, checked equal to `contract.ROW_KEYS`). Every stage's provenance events are hashed into the evidence manifest, and Freeze 2 checks the namespace (schema freeze2/v3). Relabelling a synthetic root as real, or editing provenance, is refused or detected | `runner.py`, `evidence.py`, `outcomes.py`, `freeze.py` | `test_end_to_end.py` (4 new: provenance bound; a relabelled root refused; forged provenance refused; an edited event detected), `test_pins_and_provenance.py` | Fixed |
| **R4.2** Smoke test used the focal instructions before approval | Replaced A.however.4 and B.max10 with non-focal references (`nb.min10`, `inc.silver+morning+quiet`); the plan refuses any A or B candidate | `smoke.py` | `test_pins_and_provenance.py` | Fixed |
| **R4.3** Backend logs were overwritten on retry | One directory per attempt (`attempts/NNN/`: plan, design, backend log); the provenance event names it | `runner.py` | `test_pins_and_provenance.py` (crash then resume keeps both logs) | Fixed |
| **R4.4** No retry limit for a deterministic technical failure | `max_technical_attempts` = 3 (D04, proposed): a row whose own outcome was TECHNICAL 3 times is not sent again; the run reports it, and the stage stays incomplete (no partial-completion rule) | `runner.py`, `evidence.py`, `config.py` | `test_pins_and_provenance.py` | Fixed; D04 awaits approval |
| **R4.5** The near-threshold advice was not encoded | `FEASIBILITY_NEAR_THRESHOLD` in Freeze 2 flags when the weakest contrast is supported in at most 12 + 2 configurations (`near_threshold_margin`, D14). For review, never a gate. Its behaviour is measured in the coverage study §6.7 | `freeze.py`, `config.py` | `test_pins_and_provenance.py` | Fixed; D14 awaits approval |

**Test fixtures adjusted (each a test-design consequence, not a relaxed
assertion):**

- `test_topics.py::test_a_review_decision_is_bound_to_the_question_text`
  edited a question by appending a word. With the rare-stem screen, the first
  recorded decision in sort order is now an internal pair, and an appended
  word can drop a Jaccard flag. The test now takes the first *historical*
  decision and changes the text without changing its words (a space before
  the question mark). It still asserts that the decision voids.
- `test_topics.py::test_overlap_report_is_clean` asserts a maximum historical
  Jaccard below 0.5. Two replacements first exceeded it (both reviewed as
  distinct); they were reworded rather than the assertion relaxed.

## R.2 Files

**New:**

- `src/dci/batch1/coverage_study.py`;
- `src/dci/batch1/data/topics_semantic_review.json`;
- `tests/batch1/test_pins_and_provenance.py`, `tests/batch1/test_coverage_rules.py`;
- `docs/batch1/RESEARCHER_REVIEW.md`, `TOPIC_REVIEW.md`,
  `COVERAGE_SIMULATION_REVIEW.md`, `PROTOCOL_REVIEW.md`,
  `FINAL_APPROVAL_CHECKLIST.md`;
- `docs/batch1/coverage_simulation.json`, `coverage_simulation_cap480.json`;
- `docs/batch1/figures/coverage_fig1–5.png`;
- `.python-version`.

**Renamed:** `docs/batch1/topic_review.md` is now `topic_screen_report.md`.
The old name collides with `TOPIC_REVIEW.md` on a case-insensitive
filesystem.

**Modified:**

- `src/dci/batch1/`: `store.py`, `config.py`, `environment.py`, `freeze.py`,
  `runner.py`, `evidence.py`, `outcomes.py`, `smoke.py`, `cli.py`,
  `topics.py`, `report.py`, `simulate.py`;
- `src/dci/batch1/data/`: `topics_source.json`, `topics_review.json`;
- `tests/batch1/`: `test_topics.py`, `test_end_to_end.py`,
  `test_review_artifacts.py`;
- the regenerated artifacts in `docs/batch1/`;
- `docs/batch1/README.md`, this report;
- `CHANGES_SCIENTIFIC.md`, `RESEARCH_STATE.md`, `README.md`.

**Not touched:** `dci1/`, `exploratory/`, `configs/`, the rest of `src/`.
Historical manifests, signed records and results are not touched either.

## R.3 Tests

All on this Mac, CPython 3.11.12, 2026-10-19. 36 tests are new in this
round: `test_pins_and_provenance.py` 19, `test_coverage_rules.py` 9,
`test_topics.py` 4, `test_end_to_end.py` 4.

| suite | result |
|---|---|
| Batch 1 CPU tier, full (`tests/batch1 -m "not slow"`) | **569 passed** (9 min). This run started before the last two changes below |
| after those changes: `test_review_artifacts`, `test_freeze`, `test_pins_and_provenance`, `test_integrity`, `test_end_to_end`, `test_topics`, `test_coverage_rules` | **111 passed** (54 + 57), including the 4 new end-to-end provenance tests |
| Batch 1 slow (full-size synthetic demo) | **1 passed** (5 min) |
| root suite without Batch 1, CI selection (`tests --ignore=tests/batch1 -m "not slow and not gpu and not rocm and not cuda and not cloud"`) | **2,722 passed** (1.5 min). With the 569 Batch 1 tests, the CPU tier is 3,291 |
| `exploratory/tests` (root `.venv`, as CI runs it) | 637 passed, 19 skipped, **6 failed**: the same `test_runlock_ownership.py` ids that failed before Batch 1 existed (pre-existing; nothing under `exploratory/` changed) |
| `dci1/tests_v8dev` (`dci1/.venv`, `-m "not slow and not gpu"`) | 432 passed, 5 skipped, **5 failed and 3 errors**: all in `test_legacy_prescreen_characterization.py`, the same set as in the first audit and the first remediation (pre-existing; nothing under `dci1/` changed) |

The first attempts at the root and DCI-1 suites were stopped by Claude Code
when the machine ran low on memory (the DCI-1 suite peaks at about 5 GB).
Those attempts also omitted CI's marker selection. The results above are
reruns with CI's selection after memory was freed.

The two changes after the full run:

- **The Freeze 1 interpreter record.** It now holds only the minor version
  and implementation. The full path and patch release made
  `freeze1_proposed.json` machine-specific, and the path exposed a home
  directory.
- **The four end-to-end provenance tests.**

No file under `dci1/`, `exploratory/` or the rest of `src/` changed in this
round. The new root `.python-version` file does not change the interpreter
uv chooses for any sub-project: they have their own `requires-python`, as
checked with uv 0.9.18.

## R.4 Reproducibility evidence

- **Code fingerprints:** all 47 files bound by Freeze 1 or the seam hash
  identically under CPython 3.11.12, 3.12.9 and 3.13.12 (test above; the
  auditor's `astver.py` showed three values per file under the old scheme).
- **Simulation:** the coverage study is deterministic, with seeds derived
  from the scenario, allocation and replicate number. The selection modules
  it runs (`calibration.py`, `references.py`, `simulate.py`) are unchanged
  since the run. `coverage_study.py` changed only to add the table and figure
  functions, and every table in `COVERAGE_SIMULATION_REVIEW.md` is printed by
  `--tables` from the stored JSON.
- **Topic bank:** `TOPIC_REVIEW.md`'s replacement tables were generated from
  `topics_source.json`, not transcribed. The split manifest is unchanged:
  the same 32, 64 and 480 ids.

## R.5 Commands for a third check

```bash
P=.venv/bin/python                                    # CPython 3.11
$P -m pytest tests/batch1 -q -m "not slow"           # Batch 1 CPU tier
$P -m pytest tests/batch1/test_pins_and_provenance.py tests/batch1/test_coverage_rules.py \
    tests/batch1/test_topics.py tests/batch1/test_end_to_end.py -q   # R1-R4 regressions
$P -m dci.batch1 write-review-artifacts --out "$(mktemp -d)"         # compare with docs/batch1
$P -c "from dci.batch1 import topics as T; r=T.overlap_report(T.load_bank()); print(r['clean'], r['semantic_review'])"
$P -m dci.batch1.coverage_study --out docs/batch1/coverage_simulation.json \
    --cost docs/batch1/coverage_simulation_cap480.json --tables       # every table in the D11 note
$P -m dci.batch1.coverage_study --reps 1000 --workers 8 --out "$(mktemp -d)/cov.json"   # ~17 min
# the auditor's rare-stem probe, against the current bank:
$P ../audit-batch1-2026-10-19/probes/reaudit/probe_r4b_rare.py ../audit-batch1-2026-10-19/probes/reaudit
```

The probe listed 14 pairs before this round. It now lists 5 pairs (each
historical question appears once per bank that contains it) involving three
questions:

- *animator* and *tennis balls*, both CLOSE in the semantic review and kept
  with rationales;
- the replacement *potter centring clay*, against "Describe why potters fire
  clay twice", reviewed as distinct.

All five are recorded decisions in `topics_review.json`. The wrong-Python
refusal is tested in `test_pins_and_provenance.py` by substituting the
interpreter identity. A real 3.12 interpreter would need the project's
dependencies installed first.

## R.6 Decisions awaiting the researcher

All 14 are formally PROPOSED. Python 3.11 for the orchestrator, part of D12,
was approved by the researcher in conversation and is recorded in the code;
it still needs recording in `approvals.json`. D11 needs a choice of rule (the
recommendation is a P3 minimum of 3). D05 needs the review of the 88
replacements. See [`FINAL_APPROVAL_CHECKLIST.md`](FINAL_APPROVAL_CHECKLIST.md).

## R.7 What remains uncertain

- **Matching precision (D10)** is the root cause of noisy memberships
  (Jaccard about 0.5 against the truth) and of false feasibility. It is
  disclosed, not fixed; any fix is a separate decision.
- **The semantic topic review was done by AI reviewers.** It is not a human
  review.
- **The generation host does not exist yet:** no CUDA vLLM environment, no
  attestation, no smoke test, and no throughput or truncation data.
- **All precision numbers come from invented surfaces.**

## R.8 Verdict

The re-audit's findings R1, R2 and R4 are fixed with regression tests. R3 is
characterised by a pre-registered-style simulation study and a recommendation
for the researcher's choice. The review package lets the researcher decide
every decision without reading code.

**READY FOR FINAL RESEARCHER APPROVAL. NOT YET READY FOR FREEZE 1**, which
needs:

- the researcher's approvals, including the D11 rule;
- the generation environment, attested on its host;
- the smoke test there.
