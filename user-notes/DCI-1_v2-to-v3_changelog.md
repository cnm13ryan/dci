# DCI-1 v2 to v3 changelog

**Protocol:** DCI-1  
**New version:** 3.0  
**Date:** 16 August 2026  
**Confirmatory generations completed under v2:** zero

## Summary

Version 3 preserves the directional constraint interference estimand and the confirmatory inferential design. It replaces the parts of v2 that failed to establish an operating regime or trustworthy execution provenance. The principal changes are a wider target grid, a tunable multi-family reference pool, staged solo and composed calibration, an expanded response budget, precision-based verifier validation, a strict gate state machine, four formally separate model replications, and fail-closed code and environment provenance.

## Detailed changes

### Header and protocol status

- Advanced the protocol from v2.0 to v3.0.
- Declared v3 to be informed by all completed v2 qualification, pilot, and calibration records.
- Recorded that v2 ended with four terminal model replications and zero confirmatory generations.
- Added Section 33 to close v2 formally and distinguish v2 design evidence from confirmatory evidence.

### Section 1: Definitions

- Replaced the ambiguous response-level definition of `replicate` with `model replication`.
- Added definitions for cached draw, primary observation, pseudo-run, reference family, severity level, reachability, qualification, gate record, and artifact states.
- Defined `generated`, `committed`, `accepted`, and `superseded` as distinct artifact states.

### Section 3: Scope

- Replaced the single-model scope with four separately analysed model replications.
- Required the three final references to come from three distinct registered families.
- Excluded cross-model pooling and model-general claims from v3.
- Preserved the fixed load, language, prompt template, topic space, target, and focal constraint.

### Section 4: Models and inference

- Replaced the stale Qwen2.5 model entry with:
  - `google/gemma-3n-E2B-it`;
  - `Qwen/Qwen3-4B`, with thinking disabled;
  - `Qwen/Qwen3-4B-Instruct-2507`;
  - `google/gemma-3n-E4B-it`.
- Corrected the first Qwen description from pretrained-base framing to hybrid model with thinking disabled.
- Required a canonical repository revision in the signed registration manifest before qualification.
- Replaced the nominal Transformers backend with the actual vLLM scientific execution policy.
- Replaced the fixed 400-token cap with model-specific selection from 512, 768, and 1,024 tokens.
- Formalised sixteen cached stochastic draws per confirmatory cell and one response-independent hash-selected primary observation.
- Added a preregistered execution order with E2B first.
- Added an E2B efficiency stop: reference-pool or composed-headroom failure stops the remaining v3 replications and sends any redesign to v4.
- Added a cross-replication firewall. Study-wide rules freeze before E2B and remain fixed across all v3 replications.

### Section 5: Target, focal, and reference constraints

- Retained target (A): use *however* exactly (n) times.
- Expanded the target grid from (n\in\{1,2,3\}) to (n\in\{1,ldots,8\}).
- Retained focal (B) and (m\in\{7,8,9,10\}).
- Removed the fixed twelve-candidate reference pool as the complete control pool.
- Added eight tunable reference families with four severity levels each:
  - initial-letter budget;
  - suffix budget;
  - one-letter-word budget;
  - doubled-letter budget;
  - comma budget;
  - upper-case-letter budget;
  - letter-a word budget;
  - final-y word budget.
- Limited final selection to one severity per family and three distinct families.
- Preserved deterministic verification, parse independence, whole-answer scope, joint satisfiability, non-entailment, and four frozen wordings.

### Section 6: Topic allocation

- Increased the topic bank from 576 to 624 topics.
- Increased each subject stratum from 48 to 52 topics.
- Preserved 384 confirmatory and 96 sequestered topics.
- Expanded calibration from 96 to 144 topics and divided it into:
  - 24 pre-screen topics;
  - 96 final solo-calibration topics;
  - 24 composed-reference validation topics.
- Strengthened sequestered-topic access controls. Their text remains inaccessible throughout v3.

### Section 7: Wording allocation

- Preserved the confirmatory order and wording allocation.
- Added a pilot-specific wording formula that reaches all four wording indices within twelve blocks.
- Added executable coverage assertions for wording and order balance at every generative stage.

### Section 8: Confirmatory design

- Preserved the six arms and 384 confirmatory blocks.
- Clarified the distinction between 2,304 logical cells, 36,864 cached draws, and 2,304 primary observations per model.
- Preserved the 96-block greedy-decoding sensitivity run.

### Sections 9 and 10: Scoring and verifier validation

- Preserved primary scoring rule (S_0), robustness rules (S_1) to (S_3), and intention-to-treat failure handling.
- Replaced the rigid requirement for exactly 75 natural passes and 75 natural failures.
- Added a closed natural-response reservoir and a fixed seeded sample of up to 150 responses per verifier class.
- Applied the one-sided 95% Wilson disagreement bound once after all selected labels are complete, avoiding outcome-dependent annotation stopping.
- Prohibited hand-authored cases from filling a scarce natural class.
- Retained synthetic and adversarial examples as supplementary boundary tests.
- Added a hash-conditional carry-over rule for the completed E2B v2 packet.
- Moved item-behaviour headroom from the measurement gate to scientific calibration.

### Section 11: Estimands and reachability

- Preserved the block contrast, order-specific primary estimands, per-reference exchangeability contrasts, (\pm0.10) SESOI, and (\pm0.05) exchangeability margin.
- Added the composed-reference baseline
  
  \[
  \bar p_R=\frac13\sum_j P(F_A=1\mid A+R_j).
  \]

- Added the reachability result (\tau\in[-\bar p_R,1-\bar p_R]).
- Required every composed-reference target-failure rate to lie in ([0.15,0.85]), preserving reachability of both (+0.10) and (-0.10).
- Distinguished pre-confirmatory (B)-to-(R) comparability from post-confirmatory (R)-to-(R) exchangeability.

### Sections 12 to 16: Inference and diagnostics

- Preserved block assignment, pairing, clustering, generalisation, and bootstrap resampling.
- Clarified that cached draws lie below the observation level.
- Stated that (M=16) enters no sample-size, estimator, standard-error, interval, or claim calculation.
- Applied the original power and precision calculation independently to each model.
- Kept multiplicity families separate within each model and excluded a cross-model family.
- Preserved the equivalence region and made direction and SESOI magnitude explicit as separate interval-based claim axes, resolving an inconsistency between the v2 null-result and terminal-outcome tables.
- Preserved the partial-identification treatment of scorability asymmetry.
- Added finish-reason counts and response-length quantiles (p_{50},p_{90},p_{95},p_{99}) to gate and confirmatory reports.

### Section 17: Qualification and procedural pilot

- Added a non-scientific qualification stage before Gate 0.
- Required clean committed code, a resolvable model revision, a non-empty dependency manifest, valid schemas, and functioning storage before pilot generation.
- Expanded the pilot from 72 individual generations to 72 logical cells with 1,152 cached draws so it certifies the cached architecture.
- Added fixed fixture constraints for the apparatus pilot.
- Removed truncation rate from the apparatus-pass decision.
- Added a separate pilot mask, commit, and unmask cycle.
- Defined pilot records separately from freeze records and removed confirmatory-only fields from pilot artifacts.

### Section 18: Gate and calibration redesign

- Replaced the four informal gates with a mechanically enforced state sequence:
  1. qualification;
  2. apparatus pilot;
  3. regime pre-screen;
  4. measurement validation;
  5. final solo calibration;
  6. composed-reference validation;
  7. immutable freeze;
  8. confirmatory generation;
  9. masked analysis;
  10. unmasked analysis.
- Required a hash-verified predecessor PASS record for every stage transition.
- Added a 24-topic cheap pre-screen for response length and severity viability.
- Restricted pre-screening to conservative elimination. Final parameter selection uses the independent 96-topic calibration.
- Added full target and focal calibration curves, deterministic selection, and deterministic tie-breakers.
- Preserved the (\pm0.10) solo-difficulty caliper, whole-answer scope, and 20% instruction-length caliper.
- Selected at most one severity from each eligible reference family.
- Added a 24-topic (A+R) validation stage.
- Prohibited (A+B) generation and every DCI contrast during calibration.
- Used composed-reference performance only as an eligibility predicate.
- Ranked final references by solo (B)-to-(R) distance after composed validation.

### Section 19: Masking

- Preserved the two-phase confirmatory masking procedure and single one-way confirmatory unmask.
- Added separate `pilot_mask` and `confirmatory_mask` namespaces.
- Prevented pilot mask events from consuming or modifying the confirmatory unmask event.

### Sections 20 to 23: Analysis and secondary sensitivity

- Added a complete 384 by 6 by 16 cache-matrix assertion.
- Added response-independent primary-draw selection before scoring.
- Prevented pseudo-run data from replacing primary observations.
- Added 1,000 pseudo-runs as secondary decoding-sensitivity analyses.
- Preserved the 10,000-resample order-stratified block bootstrap, scoring robustness, failure taxonomy, and qualitative error analysis.
- Generalised the Gate 1 scoring-bias table to the variable-sized natural annotation packet.

### Section 26: Terminal outcomes

- Replaced `Regime not found` with:
  - `TARGET_RANGE_EXHAUSTED`;
  - `FOCAL_RANGE_EXHAUSTED`;
  - `GRID_RESOLUTION_INSUFFICIENT`;
  - `REFERENCE_POOL_MISMATCH`;
  - `COMPOSED_HEADROOM_FAILURE`;
  - `RESPONSE_LENGTH_INCOMPATIBLE`.
- Added separate qualification, apparatus, measurement-failure, and insufficient-measurement-evidence statuses.
- Restricted every terminal statement to the declared grid, pool, cap range, or measurement evidence.
- Added a mandatory terminal payload containing curves, thresholds, reference distances, truncation summaries, hashes, permitted claims, and unanswerable estimands.

### Sections 27 and 28: Execution and provenance

- Added monotonic generated, committed, accepted, and superseded artifact states.
- Added an append-only stage-transition log.
- Standardised required gate, freeze, terminal, confirmatory, masked, and unmasked record filenames across every model tree and made stale paths fatal.
- Required the entire `dci1/` implementation to be tracked in Git.
- Required a clean worktree before any v3 artifact is created and made `writer_dirty=True` fatal.
- Recorded the actual producing commit and verified that invoked source files belong to it.
- Replaced the empty `pip freeze` digest with hashes of `uv.lock` and deterministic `uv export --frozen` output.
- Made an empty dependency representation a qualification failure.
- Added Python, vLLM, PyTorch, ROCm, driver, kernel, GPU, model, chat-template, interpreter, command, and relevant environment-variable provenance.
- Retained a container digest only when a container actually produces the artifact.
- Added tests that dependency changes alter the digest and deterministic derivations reproduce their hashes.

### Sections 30 to 32: Limitations, release, and checklist

- Updated the limitations from one model and one reference family to four separately analysed models and a multi-family reference pool.
- Reframed comparability as a pre-confirmatory selection stage followed by a post-confirmatory exchangeability test.
- Updated the release manifest for 528 released and 96 sequestered topics.
- Added cached draws, primary selection, gate records, terminal reports, Git provenance, `uv` manifests, and pseudo-run summaries to the release.
- Updated the construct-validity checklist for the new topic counts, measurement criterion, replication structure, and terminal taxonomy.

### Section 33: Historical closure

- Recorded both Qwen target-grid failures and reference mismatch.
- Recorded the unresolved Qwen Gate 1 class shortfall, including the packet with only 17 naturally occurring failures.
- Recorded E2B target and focal headroom and its reference mismatch.
- Recorded Gemma truncation rates at the v2 400-token cap.
- Corrected D27 to include the uncommitted E4B 64-response calibration attempt.
- Marked the E4B fragment `SUPERSEDED_NON_EVIDENCE`.
- Recorded the untracked implementation, dirty writers, and empty dependency digest as provenance defects repaired in v3.

## Components preserved from v2

The following remain unchanged in scientific substance:

- directional constraint interference as a target-failure risk difference;
- empty background set and primary load of two;
- focal (A+B), three (A+R_j), target-alone, and topic-alone arms;
- block contrast (D_i=F_{i,B}-\frac13\sum_jF_{i,R_j});
- target-first and added-first primary estimands;
- 384 confirmatory blocks and 192 blocks per order;
- deterministic target scoring and three registered alternatives;
- intention-to-treat analysis;
- block as pairing, clustering, and generalisation unit;
- 10,000-resample stratified block bootstrap;
- multiplicity families and simultaneous intervals;
- (\pm0.10) smallest-effect and equivalence region;
- (\pm0.05) exchangeability region;
- non-behavioural-failure symmetry and partial-identification bounds;
- fixed-size sampling with no interim stopping;
- confirmatory masking and one-way unmasking;
- error taxonomy, contamination checks, human feasibility baseline, and held-out sequestered topics.
