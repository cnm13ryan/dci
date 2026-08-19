# DCI-1 v2 — preregistration requirement → implementation → executable validation

Source of truth: `user-notes/DCI-1_preregistration_v2.md` (§ numbers below),
amended by the task brief §1 (models, vLLM backend, no-thinking) and §2
(cached-generation resampling), and by the researcher-authorized amendment A2
(`DECISIONS.md`: backend pinned to vLLM 0.15.1+rocm720; registered models
Qwen3-4B, Qwen3-4B-Instruct-2507, gemma-3n-E2B-it, gemma-3n-E4B-it).
Implementation paths are relative to `dci1/src/dci1/`; tests relative to
`dci1/tests/`.

| Prereg requirement | Implementation | Executable validation / test |
|---|---|---|
| §2 phenomenon: τ as risk difference on target failure | `analysis/estimators.py` (`block_contrast`, `tau_by_order`) | `test_analysis_estimators.py` |
| §2 two components measured separately (swap effect, exchangeability) | families F1 and F2 in `analysis/families.py` | `test_analysis_families.py` |
| §3 exclusions: fixed load 2, satisfiability, non-entailment certified | `constraints/witnesses.py`; two-constraint prompts only in `design/prompts.py` | `test_witnesses.py`; `test_protocol_fidelity.py::test_load_is_two_in_contrast_arms` |
| §4 decoding policy: T=0.7, top-p 0.9, top-k 50 explicit, 400 max new tokens, 1 sample/cell, zero-shot single turn | `protocol/constants.py::DECODING`; `models/adapters.py` writes them into every plan.json | `test_model_plans.py::test_decoding_policy_pinned`; GPU echo-check in qualification report (`models/qualification.py`) |
| §4 (amended §1.1/§1.2) four models, vLLM backend, pinned revisions | `models/adapters.py::MODELS` (4 `ModelSpec`s, revisions pinned) | `test_model_plans.py::test_revisions_pinned`; backend asserts revision via engine kwargs; qualification checks recorded revision |
| §4 seed = deterministic from root seed + prompt hash (amended §2.4: + model + pool index) | `protocol/seeds.py::generation_seed` | `test_seed_levels.py` |
| Amendment §1.3 no-thinking per model, qualification probes | `models/adapters.py` (`chat_template_kwargs`, `reasoning_mode=NO_THINKING`); `models/qualification.py` | `test_qualification_contract.py` (validates recorded qualification artifacts); live GPU run via `cli.py qualify` |
| §5 target A, focal B, twelve-candidate pool | `constraints/definitions.py` | `test_verifiers_pool.py` |
| §5 parse independence (no candidate mentions h,o,w,e,v,r or "however") | property check in `constraints/definitions.py::assert_parse_independence` | `test_protocol_fidelity.py::test_parse_independence` |
| §5 joint satisfiability + non-entailment witnesses, both directions | `constraints/witnesses.py` | `test_witnesses.py` (verifies every witness with the real verifiers) |
| §5 four frozen wordings per constraint; identical verifier behaviour on 20 test responses | `constraints/wordings.py`; `constraints/wording_check_responses.py` | `test_wordings.py` |
| §6 topic bank: 576 questions, 12 strata × 48; four authoring rules | `topics/data/topics.json`; `topics/bank.py` (rule checks) | `test_topics.py` |
| §6 stratified seeded split 8/32/8 per stratum → 96/384/96, disjoint | `topics/split.py` | `test_topics.py::test_split_sizes_stratification_disjointness` |
| §7 prompt = question + numbered constraints + `Answer:`; byte-identity except added line; order/wording by block index | `design/prompts.py`, `design/blocks.py` | `test_protocol_fidelity.py::test_prompt_bytes`, `::test_order_balance`, `::test_wording_assignment` |
| §8 six arms per block; 384×6 cells; diagnostics excluded from contrasts | `design/blocks.py::ARMS`; `analysis/estimators.py` reads only the four primary arms | `test_protocol_fidelity.py::test_six_arm_structure`; `test_unit_separation.py` |
| §8 greedy sensitivity run (96 blocks × 4 arms) | `design/plan.py::greedy_plan`; scored via same pipeline, reported secondary | `test_protocol_fidelity.py::test_greedy_plan` |
| §9 S0 scoring rule; failure includes empty/refusal/truncated/unprocessable; S1–S3 declared; graded \|count−n\| recorded | `verifiers/target.py` | `test_verifiers_target.py` (incl. the 40-case boundary suite) |
| §10 verifier blindness (no arm label input), determinism ×3 processes, human agreement, item behaviour, 4 validity checks | `verifiers/` (signatures take response text + own params only); `calibration/gate1.py` | `test_verifiers_blindness.py`; `gate1` artifacts; human parts PENDING_HUMAN (D25) |
| §11 estimands τ_target-first, τ_added-first, δ12 δ13 δ23; SEI 0.10; margin 0.05; claim levels | `analysis/estimators.py`, `analysis/claims.py`; constants in `protocol/constants.py` | `test_analysis_estimators.py`; `test_claims.py` |
| §12 block is assignment/pairing/clustering/generalisation unit; three executable checks (resampling unit, function signature, variance behaviour) | `analysis/bootstrap.py` (block resampling, stratum counts asserted); estimators accept `BlockTable` only | `test_unit_separation.py` (all three §12 checks) |
| §13 planning quantities; realised discordance + achieved detectable effect reported | `analysis/precision.py` | `test_precision.py` |
| §14 families F1–F6 closed at freeze; simultaneous max-\|t\| intervals; marginal alongside | `analysis/families.py`, `analysis/bootstrap.py::simultaneous_intervals` | `test_analysis_families.py`; `test_bootstrap.py` |
| §15 equivalence rules; three fixed outcome wordings; guarded claim emitter | `analysis/claims.py` (single emitter with precondition, aborts otherwise) | `test_claims.py::test_absence_string_requires_precondition` |
| §16 manipulation check (uptake), compliance checks, instrument check, feasibility check, F6 symmetry + partial identification bounds | `analysis/checks.py` | `test_checks.py` |
| §17 procedural pilot: 12 topics, 72 cells, four inspected quantities, seven acceptance conditions, no contrasts | `pilot/runner.py` (amendment reading per D09/D10) | `test_pilot_logic.py` (acceptance logic on synthetic rows); live via `cli.py pilot` |
| §18 Gate 1 (40 boundary cases, determinism 1.000, human ≤2/75 per class) | `calibration/gate1.py`; boundary suite in `verifiers/boundary_suite.py` | `test_verifiers_target.py::test_boundary_suite`; determinism via 3 subprocesses in `gate1`; human part PENDING_HUMAN |
| §18 Gate 2 (n closest to 0.30 in [0.15,0.50]; m closest to 0.30 in [0.15,0.55]; admission ±0.10 solo rate, ±20% length, whole-answer; ≥3 admitted; certification) | `calibration/gate2.py`; `calibration/design.py` (96 topics × 19 solo prompts) | `test_calibration_gates.py` |
| §18 Gate 3 freeze: all listed fields recorded and hashed; per-model records (amendment §6); §2.10 resampling fields present | `freeze/record.py` | `test_freeze.py` (completeness, immutability, no cross-model inheritance, refusal on mismatch) |
| §19 masked analysis: permuted labels, mask key custody, single unmask function, three executable checks | `masking/mask.py` | `test_masking.py` (≥half blocks differ; key opened exactly once; code-hash rerun byte-compare) |
| §20 fixed-order analysis, complete-matrix assertion, fail-closed named statuses | `analysis/run.py` | `test_analysis_run.py` (missing cell / duplicate / non-finite → INCONCLUSIVE_*, no claim) |
| §21 post-treatment quantities excluded from primary formulas via causal-role assertion | `protocol/codebook.py::assert_primary_fields`; `analysis/estimators.py` consumes it | `test_codebook.py::test_post_treatment_excluded` |
| §22 secondary analyses list | `analysis/secondary.py` | `test_secondary.py` |
| §23 nine-category priority taxonomy; four follow-up analyses | `analysis/taxonomy.py` | `test_taxonomy.py`; hand-coding packet PENDING_HUMAN |
| §24 contamination: new topics, topic-alone arm, canary, sequestered withheld | `topics/bank.py` rules; canary in `protocol/constants.py`; release tooling `reports/release.py` | `test_topics.py`; release-time web search reported at release |
| §25 human labels & baseline | packet builders in `calibration/gate1.py` / `reports/human_baseline.py` | PENDING_HUMAN (D25) |
| §26 terminal outcomes table | `analysis/claims.py::terminal_outcome` | `test_claims.py` |
| §27 execution integrity: per-generation record fields; eight abort conditions | `evidence/store.py`, `evidence/integrity.py` | `test_evidence_store.py`, `test_integrity.py` |
| §28 codebook (6 fields/row, 4 executable checks); environment record; raw data immutability | `protocol/codebook.py`; environment digest per D22 in `freeze/record.py`; `evidence/store.py` | `test_codebook.py`; `test_evidence_store.py::test_raw_rows_immutable` |
| §31 release list | `reports/release.py` | release-time |
| Amendment §2.2–§2.5 pools: M=16 per (model,block,arm), immutable, content-hashed, repairable, fail-closed on incompleteness | `generation/pools.py`, `generation/validation.py`, `evidence/store.py` | `test_pools.py` (§8.3 items) |
| Amendment §2.6 pseudo-run resampling, manifest schema | `resampling/pseudo.py` | `test_resampling.py` (§8.4 items) |
| Amendment §2.7 primary selection, lineage separation, bit-identical invariance | `resampling/primary.py`; distinct lineages `selection/primary/` + `derived/primary/` vs `selection/pseudo_runs/` + `derived/pseudo_runs/` in the evidence tree | `test_unit_separation.py::test_primary_invariant_under_pseudo_runs`, `::test_pseudo_cannot_write_primary` |
| Amendment §2.8 permitted uses (sensitivity only) | `analysis/sensitivity.py` | `test_sensitivity.py` |
| Amendment §2.10 design-defining fields explicit, no defaults | `protocol/constants.py::StudyConfig` (constructor requires every field) | `test_freeze.py::test_missing_field_raises` |
| Amendment §3 three randomness levels separated | `protocol/seeds.py` (disjoint domains + roots) | `test_seed_levels.py` |

## Amendment consequences for "one accepted response per block × arm" (task §2.9)

1. The experimental observation is unchanged: exactly one accepted response per
   (model, block, arm) cell enters scoring; the accepted table has exactly
   `blocks × 6` rows (asserted in `analysis/run.py` step 2 and
   `test_unit_separation.py`).
2. The cached pool sits **below** the observation: it is the empirical
   approximation of the conditional response distribution from which the one
   accepted response is realised. Pool rows never reach any estimator, are
   never treated as replicates or blocks, and M appears in no estimator,
   interval or claim rule.
3. The primary realised dataset is fixed by a rule (`primary_pool_index = 0`)
   frozen before any outcome exists; because member 0 is the first independent
   seeded draw, the primary dataset's sampling distribution is identical to the
   unamended protocol's single generation per cell — the estimand, the
   aggregation unit, the clustering structure and the estimator are untouched.
4. Within-cell decoding variability is still absorbed into the block-level
   contrast and priced by the block bootstrap, exactly as prereg §12 states;
   the pool does not create a replicate level in the primary analysis.
5. Pseudo-runs are additional *realisations* of the same design, used only for
   the prespecified stochastic-stability sensitivity analysis; each pseudo-run
   also has exactly one response per cell, and no pseudo-run may replace,
   modify or be promoted to the primary dataset (write-path guard + bit-identity
   check).
6. The block bootstrap is unchanged: 10,000 resamples of block identifiers,
   stratified by presentation order, all six arms travelling together; it never
   resamples pool members, and its RNG stream is disjoint from the resampling
   RNG (D06/D08).
