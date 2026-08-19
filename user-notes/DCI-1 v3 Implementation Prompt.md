Implement DCI-1 v3 from `DCI-1_preregistration_v3.md` and `DCI-1_v2-to-v3_changelog.md`. These are the only documentary dependencies. `DCI-1_preregistration_v3.md` is the sole scientific authority. The changelog is an anti-regression specification for changes from v2. No other document, prompt, implementation note, historical specification, or prior artifact may supply scientific rules, defaults, model identities, thresholds, stage semantics, or missing values.

1. The v3 implementation shall be scientifically independent of all previous implementations. It shall have its own study namespace, protocol constants, state, evidence tree, prompts, verifiers, calibration logic, freeze logic, masking state, analysis state, and reports. Generic infrastructure may be shared only when its semantics are independent of DCI protocol version. V3 scientific code shall not import, call, inherit from, read configuration from, or fall back to an earlier DCI implementation. Historical evidence shall remain immutable.

2. The only permitted scientific evidence carry-over is the E2B Gate 1 packet authorised by v3. It may enter v3 only when the construct definition, normalisation, target-verifier source, boundary specification, and relevant configuration hashes are byte-identical. The v3 carry-over record shall identify the source packet, record every required hash, preserve its provenance, and become part of the v3 evidence tree. Any mismatch requires a new v3 measurement packet.

3. One canonical registered execution interface shall expose qualification, pilot, regime pre-screen, Gate 1 measurement, Gate 2A solo calibration, Gate 2B composed validation, freeze, confirmatory generation, primary selection, confirmatory masking, masked analysis, unmasking, final analysis, pseudo-runs, evidence verification, and reporting. Every public command shall dispatch through the same canonical state machine and evidence architecture. Registered commands shall not call generation, storage, selection, masking, analysis, or reporting implementations directly.

4. The procedural pilot, synthetic end-to-end tests, calibration stages, confirmatory execution, primary selection, masking, masked analysis, unmasking, final analysis, pseudo-runs, evidence verification, and reporting shall use the same production stage functions, state-transition engine, evidence writers, cache machinery, primary selector, masking implementation, custody implementation, and analysis entrypoints. Stage-specific configuration, inputs, artifact types, and namespaces are permitted. Parallel pilot-only, synthetic-only, calibration-only, or confirmatory-only implementations are prohibited.

5. Every mutating registered operation shall follow one production path:

```text
public entrypoint
→ canonical dispatcher
→ exclusive writer lock
→ clean-worktree check
→ canonical evidence verification
→ state and predecessor validation
→ production stage function
→ canonical evidence writer
→ durable write
→ content-hash verification
→ artifact acceptance
→ signed stage or operation record
→ append-only transition log
```

6. The permitted scientific stage sequence is:

```text
QUALIFIED
→ GATE_0_APPARATUS_PASS
→ REGIME_SCREEN_PASS
→ GATE_1_MEASUREMENT_PASS
→ GATE_2A_SOLO_CALIBRATION_PASS
→ GATE_2B_COMPOSED_VALIDATION_PASS
→ GATE_3_FREEZE
→ confirmatory generation
→ masked analysis
→ unmasked analysis
```

Every stage shall verify the predecessor PASS record before mutation. Verification shall cover predecessor stage identity, PASS status, content hash, signature, model-replication identity, model revision, producing Git commit, environment digest, input hashes, and frozen provenance. Hash verification without signature verification is invalid. A terminal state shall disable all later generation commands.

7. One canonical evidence-verification routine shall implement the complete execution-integrity contract and shall be used by the public evidence-verification command and every irreversible registered transition. It shall verify protocol identity, model-replication identity, expected stage, predecessor PASS identity, predecessor hash, predecessor signature, Git cleanliness, producing commit, invoked source membership in that commit, model revision, hardware class, dependency digest, interpreter identity, prompt-plan membership, context-limit compliance, verifier source hashes, response content hashes, cached-draw identities, cached-draw counts, accepted-row uniqueness, artifact-state legality, artifact-type legality, schema validity, codebook validity, required manifests, required records, parent hashes, freeze binding, namespace correctness, durable storage, and stale or unexpected paths. Missing required evidence is a verification failure.

8. Canonical evidence verification shall run immediately before freeze acceptance, confirmatory generation, primary selection, confirmatory mask creation, masked analysis, unmasking, final analysis, pseudo-run derivation, report generation, and every other irreversible registered transition. Verification shall run against current durable state. A previous successful verification shall not authorise a later transition.

9. Evidence writers shall be serialized across processes. At most one writer may hold mutation authority for a given `(study, model replication, stage or mutating operation)`. The lock shall cover identity checks, existence checks, writes, durable commit, hash verification, artifact-state mutation, manifest updates, sealing, and transition logging. Concurrent attempts capable of producing duplicate cached-draw identities, duplicate accepted observations, duplicate state transitions, replacement manifests, replacement mask keys, or duplicate unmask events shall fail before mutation. Process-local mutexes are insufficient.

10. No v3 scientific or protocol artifact may be produced from a dirty Git worktree. This applies to every artifact type, prompt plan, gate record, calibration record, freeze, raw generation, derived table, selection record, mask record, analysis result, transition record, and report. Production code shall contain no `allow_dirty` flag, environment override, hidden bypass, or equivalent escape hatch. Synthetic fixtures shall use a structurally separate test namespace and shall never become accepted registered evidence.

11. The complete implementation used to produce v3 artifacts shall be tracked in Git before the first v3 artifact is created. Every artifact shall record the actual producing commit. Every invoked source path shall be verified as belonging to that commit.

12. `uv.lock` and deterministic `uv export --frozen` output shall define the dependency representation. Qualification shall fail when either is missing or empty. The environment record shall contain the lockfile hash, export hash, exact Python executable and version, exact scientific invocation command, vLLM version and settings, PyTorch version, ROCm version, driver version, operating system, kernel version, GPU name, GPU architecture, model repository, model revision, chat-template hash, and registered execution-relevant environment variables. A container digest shall be recorded only when that container produced the artifact. Missing interpreter binaries or required environment fields shall fail closed.

13. The four registered model replications and execution order are:

```text
1. google/gemma-3n-E2B-it
2. Qwen/Qwen3-4B
3. Qwen/Qwen3-4B-Instruct-2507
4. google/gemma-3n-E4B-it
```

`Qwen/Qwen3-4B` is the hybrid Qwen model with thinking disabled. Every model shall have an exact repository revision in the signed study-wide registration manifest before qualification. Model substitution is prohibited.

14. Scientific inference shall use vLLM, bfloat16, temperature 0.7, top-p 0.9, top-k 50, one calibration draw per cell, sixteen confirmatory cached draws per cell, and one primary observation per cell. The completion cap shall be selected mechanically from 512, 768, and 1024 tokens. Prompting shall be zero-shot and single-turn. Examples, tools, retrieval, self-consistency, best-of-N selection, revision passes, and additional turns are prohibited.

15. E2B shall run first. `REFERENCE_POOL_MISMATCH` or `COMPOSED_HEADROOM_FAILURE` for E2B shall prevent the remaining model replications from starting. Study-wide rules shall freeze before E2B qualification. Outcomes from one v3 replication shall not alter later v3 protocol rules. Model adaptation is limited to `n`, `m`, completion-token cap, one severity per eligible reference family, and final identities of three references under the registered selection algorithms.

16. The target constraint is `Use the word however exactly n times` with `n ∈ {1,2,3,4,5,6,7,8}`. The focal constraint is `Every word in the answer must have at most m letters` with `m ∈ {7,8,9,10}`.

17. The eight reference families and severity grids are:

```text
RF1: at most q words begin with b; q ∈ {8,5,2,0}
RF2: at most q words end with ing; q ∈ {8,5,2,0}
RF3: at most q words have one letter; q ∈ {8,5,2,0}
RF4: at most q words contain identical adjacent letters; q ∈ {6,4,2,0}
RF5: at most q comma characters; q ∈ {12,8,4,0}
RF6: at most q upper-case English letters; q ∈ {12,8,4,0}
RF7: at most q words contain a; q ∈ {24,16,8,0}
RF8: at most q words end with y; q ∈ {8,5,2,0}
```

At most one severity from each family may advance. The final three references shall belong to three distinct families. Parse independence, whole-answer scope, machine-verified joint satisfiability, bidirectional non-entailment, four frozen wordings, and wording-equivalent verifier behaviour on the registered twenty-response suites shall be executable preconditions.

18. The topic bank contains 624 identities across twelve subject strata with 52 identities per stratum. Each stratum contains 2 pre-screen topics, 8 final solo-calibration topics, 2 composed-validation topics, 32 confirmatory topics, and 8 sequestered topics. The resulting totals are 24, 96, 24, 384, and 96.

19. The 96 sequestered topic texts shall remain inaccessible throughout v3. The implementation may receive only opaque identities, pre-existing content hashes, and authorised opaque stratum metadata. It shall never create, regenerate, inspect, read, materialise, tokenise, prompt with, log, infer, or reconstruct the sequestered text. Missing access-control infrastructure shall fail closed. Replacement sequestered topics shall not be generated.

20. Every prompt shall contain the topic question, a numbered list of active constraints, and `Answer:` in that order. Compared prompts within a block shall be byte-identical outside the added-constraint line. Confirmatory block `i` shall use presentation order `i mod 2`, target wording `i mod 4`, and added wording `floor(i/4) mod 4`. The pilot shall use target wording `i mod 4`, added wording `(i + floor(i/4)) mod 4`, and order `i mod 2`. Every generative stage shall verify its registered wording and order coverage before generation.

21. The six confirmatory arms are `A+B`, `A+R1`, `A+R2`, `A+R3`, `A`, and topic alone. Each model shall contain 384 confirmatory blocks, 2,304 logical cells, 36,864 cached stochastic draws, and 2,304 primary observations. The target-alone and topic-alone arms are descriptive and shall not enter focal-to-reference contrasts. The greedy sensitivity run shall use the four primary arms on the first 96 confirmatory blocks for 384 additional generations.

22. The primary target verifier shall apply `S0` to the complete response: lowercase the text, identify maximal alphabetic runs, count runs exactly equal to `however`, and pass exactly when the count equals `n`. Every other state is failure, including incorrect count, empty response, refusal, token-limit truncation, and verifier-processing failure. Verifier-processing failure shall be representable in data and codebook domains.

23. `S1` shall apply `S0` without lowercasing. `S2` shall count non-overlapping occurrences of the substring `however` in lowercased text. `S3` shall apply `S0` after the registered removal of leading colon-ended preamble and constraint-restatement lines. No additional scoring rule may enter registered analysis.

24. The target verifier shall receive only response text, target identity, and the information required to apply the target rule. It shall not receive arm identity, added-constraint identity, reference identity, or secondary-verifier output. Every verifier shall be deterministic, model-independent, and free of language-model judging.

25. Qualification shall verify clean tracked code, resolvable model revision, non-empty dependency representation, prompt-plan schema, verifier tests, wording tests, cache reachability, durable-store reachability, environment hashability, and producing-commit hashability. Qualification shall inspect no behavioural rate. Failure shall return `QUALIFICATION_FAILURE`.

26. The procedural pilot shall use twelve fixed pre-screen topics, all six logical arms, both presentation orders, `n=3`, `m=9`, RF1 at `q=5`, RF2 at `q=5`, RF5 at `q=8`, a 1,024-token cap, 72 logical cells, and 1,152 cached draws. It shall inspect only committed and accepted counts, exhausted technical-generation failures, codebook validity, content-hash and cache-restoration behaviour, and successful pilot mask, commit, unmask, and structural analysis execution. It shall compute no target-failure rate, added-constraint uptake rate, arm difference, or scientific contrast.

27. Pilot acceptance requires exactly 72 committed logical cells, exactly 1,152 committed cached draws, exactly one hash-selected primary row per cell, zero exhausted technical-generation failures, valid codebook fields and domains, a structurally complete analysis result without scientific rates or contrasts, refusal of a response whose stored bytes no longer match its content hash, byte-identical durable-cache restoration without regeneration, and successful `pilot_mask` creation and unmasking with zero effect on `confirmatory_mask`. Any failure shall return `APPARATUS_FAILURE`. A repair shall require a new producing commit followed by qualification and the full pilot.

28. The regime pre-screen shall run on 24 topics with one response per registered severity cell. A fixed subject-balanced 96-prompt set shall run at each cap in `{512,768,1024}` using identical prompt identities and registered seed derivation. The smallest cap with truncation at most 0.10 shall be selected. Failure of all caps shall return `RESPONSE_LENGTH_INCOMPATIBLE`. Finish-reason counts and `p50`, `p90`, `p95`, and `p99` response-length quantiles shall be recorded at every cap.

29. The pre-screen shall estimate complete target, focal, and reference-family severity curves. Target or focal grids shall be rejected early only when every 95% Wilson interval lies entirely on the same inadmissible side of the corresponding Gate 2 band. A focal severity is provisionally plausible when its interval intersects `[0.15,0.55]`. A reference family is provisionally plausible when at least one severity and one provisionally plausible focal severity yield a 95% Newcombe interval for `p(F_R)-p(F_B)` intersecting `[-0.10,0.10]`. Fewer than three plausible families shall return `REFERENCE_POOL_MISMATCH`. Pre-screen point estimates shall not select final `n`, `m`, or references.

30. `GRID_RESOLUTION_INSUFFICIENT` shall apply when adjacent registered severities lie on opposite sides of the complete admission band. `TARGET_RANGE_EXHAUSTED` and `FOCAL_RANGE_EXHAUSTED` shall apply when the relevant curve reaches a registered grid boundary while remaining on one side of its admission band. Reports shall record the complete curve and boundary value.

31. Gate 1 shall require every verifier to pass the frozen forty-case boundary suite covering empty response, adjacent punctuation, capitalisation, hyphenation, target text inside a longer word, repeated words, non-Latin characters, and truncation mid-word. The target verifier shall also pass determinism, human agreement, face validity, content validity, convergent validity, and discriminant validity.

32. Every verifier shall run three times on every calibration response in three separate processes. Agreement shall equal 1.000.

33. Naturally generated pre-screen and dedicated measurement-validation responses shall form a closed reservoir before human labels are opened. A verifier class with fewer than 150 natural cases shall trigger the frozen set of up to 300 additional measurement-validation responses across the registered target-severity grid. After reservoir closure, each class shall use a fixed seeded sample of `min(150,N_c)`. Three annotators shall label every selected response. Annotators shall see response text and target constraint text. Arm, model label, added constraint, and automated verdict shall remain hidden. Hand-authored responses shall not fill a scarce natural-response class.

34. Gate 1 shall require the one-sided 95% Wilson upper bound on verifier-to-majority disagreement to be at most 0.10 in both natural verifier classes. A bound above 0.10 with 150 cases shall return `MEASUREMENT_NOT_ESTABLISHED`. A bound above 0.10 with fewer than 150 cases caused by exhaustion of the natural class shall return `MEASUREMENT_EVIDENCE_INSUFFICIENT`. Any verifier repair shall require a new protocol version.

35. Gate 2A shall use the independent 96-topic solo-calibration set with one response per severity and topic. Target values shall be eligible at failure rates in `[0.15,0.50]`. `n*` shall minimise distance to 0.30 with smaller `n` as the exact tie-breaker. Focal values shall be eligible at failure rates in `[0.15,0.55]`. `m*` shall minimise distance to 0.30 with smaller `m` as the exact tie-breaker.

36. Every severity of every reference family shall be measured alone. Within each family, the selected severity shall minimise absolute solo-failure distance from the selected focal severity, subject to absolute distance at most 0.10, every frozen wording having word count within 20% of the corresponding focal wording, whole-answer scope, target-verifier parse independence, joint satisfiability, and non-entailment. The less restrictive severity shall break an exact tie. Fewer than three eligible families shall return `REFERENCE_POOL_MISMATCH`.

37. Gate 2B shall evaluate every eligible reference family as `A+R_f` on the independent 24-topic composed-validation set using selected `n*` and `q_f*`. `A+B` shall not be generated or estimated during calibration. A family is composed-valid when target failure lies in `[0.15,0.85]`. Composed performance shall act only as an eligibility predicate. Final references shall be the three composed-valid families with smallest solo-failure distance from `B`, with family identifier as the exact tie-breaker. Fewer than three composed-valid families shall return `COMPOSED_HEADROOM_FAILURE`.

38. Gate 3 shall freeze model revision, completion cap, `n*`, `m*`, final reference families and severities, every wording, topic splits, prompt template, chat-template hash, verifier sources, `S0` through `S3`, decoding settings, seed rules, primary-draw rule, block plan, family declarations, equivalence regions, codebook, Git commit, clean-tree assertion, dependency digest, environment digest, hardware record, gate-record hashes, and complete analysis plan. Confirmatory generation shall be impossible until the freeze verifies successfully.

39. Every confirmatory cell shall contain sixteen predetermined cached-draw identities. The generation seed shall derive from the fixed root seed, model identifier, exact prompt hash, and cached-draw index. Missing seed inputs shall fail. Hidden seed defaults are prohibited. A missing draw may be repaired only by regenerating that exact predetermined identity with its predetermined seed. Pool shrinking, replacement seeds, reduced-pool resampling, and averaging around missing cells are prohibited.

40. The primary cached-draw index for cell `c` shall be:

```text
j_c = H("primary-root", model-id, prompt-hash) mod 16
```

Response content and verifier outcomes shall be unavailable to the selector. Primary selection shall run only after the complete required cache passes canonical evidence verification. Exactly one accepted primary observation shall exist per logical cell.

41. The sixteen cached draws lie below the observation level. They shall not increase sample size, enter the primary estimator jointly, replace a missing primary observation, or affect primary interval calculations. The block remains the assignment, pairing, clustering, bootstrap, and generalisation unit.

42. One thousand pseudo-runs shall select one cached draw per prompt cell using the frozen pseudo-run seed scheme, perform zero model inference, recompute the two primary estimands, and report empirical distributions and sign stability. Pseudo-runs shall have separate selection and derived paths, shall not mutate primary selection, shall not replace primary observations, and shall support no confirmatory claim. Generation randomness, pseudo-run selection randomness, and bootstrap randomness shall use separate domains.

43. Confirmatory masking shall permute labels of the four primary arms independently within each block after confirmatory generation and before analysis, using system randomness. The mask key shall be stored separately and its content hash shall be recorded when written. Pilot masking shall use `pilot_mask`. Confirmatory masking shall use `confirmatory_mask`. Pilot mask state shall have no read or write capability over confirmatory mask state.

44. `confirmatory_mask` creation shall be persistently single-shot across processes and restarts. An exclusive cross-process lock and immutable durable reservation shall be acquired before mask randomness is generated or evidence is mutated. Existing reservation, key, masked-view acceptance record, or completed mask event shall make a second mask attempt fail before new key generation or mutation. A crash after reservation shall leave a fail-closed state requiring audited recovery. Existing mask state shall never be deleted or overwritten to permit re-masking.

45. Masked analysis shall execute the complete planned analysis on permuted labels. Response reading, failure coding, compliance inspection, arm-symmetry inspection, and anomaly diagnosis shall occur in the masked phase. Permitted masked-phase changes are analysis-code defect repair, diagnostic output addition, and declaration of an anomaly with its handling rule. Estimands, multiplicity families, equivalence regions, reference set, scoring rules, verifiers, claim rules, and topic splits shall remain fixed.

46. Confirmatory unmasking shall be persistently single-shot across processes and restarts. An exclusive cross-process lock shall be acquired first. Canonical evidence verification, masked-analysis acceptance, parent-hash validation, prior-unmask absence, and analysis-code identity shall be verified before key access. An immutable durable unmask reservation shall be written before the key is opened. The named unmask function shall open the key exactly once, record timestamp, mask-key hash, and analysis-code hash, write the unmask record durably, and append the transition. A second unmask attempt shall fail before key access. Re-masking after unmasking shall fail before mutation.

47. The masked analysis code shall have no ability to read the mask key outside the named unmask function. The permuted labels shall differ from true labels in at least half of blocks. The analysis-code hash recorded at unmasking shall equal the hash of the code that produced all masked outputs. Re-execution from that code shall reproduce masked outputs byte for byte. Analysis-code changes after unmasking shall be labelled post-unmasking and shall support no primary claim.

48. The primary block contrast is:

```text
D_i = F_i,B - (F_i,R1 + F_i,R2 + F_i,R3) / 3
```

Each model shall have separate target-first and added-first primary estimands. Reference exchangeability shall use the three pairwise reference contrasts. The SESOI and primary equivalence region are ±0.10. The exchangeability region is ±0.05.

49. The primary analysis shall assert the complete `384 × 6 × 16` cache matrix, select one primary response per cell before scoring, apply `S0`, compute compliance and arm-symmetry quantities, form block contrasts, perform 10,000 bootstrap resamples stratified by presentation order, carry all six arms with every resampled block, compute simultaneous intervals within each registered multiplicity family, and apply the registered claim and partial-identification rules.

50. Multiplicity families shall remain separate within each model: F1 contains the two primary estimands, F2 the three exchangeability contrasts, F3 the six per-reference by order contrasts, F4 the six `S1` to `S3` by order robustness estimands, F5 the nine failure-category contrasts, and F6 the three non-behavioural-failure symmetry contrasts. Each family shall use the registered simultaneous 95% studentised maximum absolute standardized deviation bootstrap. Marginal intervals shall also be reported.

51. Response length, realised token count, truncation, finish reason, added-constraint uptake, refusal, malformed-output status, failure category, and every other post-treatment quantity shall be excluded from primary estimators as covariates, filters, stratifiers, and weights. The codebook causal role shall enforce this mechanically.

52. A missing cell, duplicate accepted response, non-finite standard error, or non-finite simultaneous bound shall fail closed for the affected quantity and produce no claim. Degenerate all-identical block contrasts shall remain in the analysis and shall be reported. The design is fixed size with no interim analysis, optional stopping, or adaptive sample size.

53. The registered secondary analyses, error taxonomy, contamination checks, human feasibility baseline, treatment-uptake checks, operating-condition checks, target-alone and topic-alone diagnostics, scoring-bias analysis, forty-case masked human failure coding, greedy-decoding sensitivity run, release requirements, and fixed terminal claim vocabulary shall follow the v3 preregistration exactly.

54. Artifact states shall be exactly `generated`, `committed`, `accepted`, and `superseded`. A generated artifact becomes committed only after durable write and content-hash verification. A committed artifact becomes accepted only after stage authorisation, authenticated predecessor verification, schema validation, frozen-plan membership where applicable, and canonical evidence verification. A superseded artifact shall never return to accepted state.

55. Artifact types shall be exactly `qualification_record`, `prefreeze_plan`, `pilot_record`, `gate_record`, `calibration_record`, `registered_freeze`, `confirmatory_evidence`, `masked_result`, `unmasked_result`, and `superseded_non_evidence`.

56. Every generation record shall contain stage, artifact state, model-replication identity, block identity, arm, cached-draw index, order, wording indices, prompt hash, model revision, backend version, scientific-interpreter identity, dependency digest, hardware class, seed, raw response text, response content hash, token counts, finish reason, and every verifier verdict with its source hash.

57. Every model evidence tree shall contain `qualification.json`, `gate0_apparatus.json`, `regime_screen.json`, `gate1_measurement.json`, `gate2a_solo.json`, `gate2b_composed.json`, `gate3_freeze.json`, `transition_log.jsonl`, and `terminal_report.json`. A model reaching confirmation shall also contain `confirmatory_manifest.json`, `masked_result.json`, and `unmasked_result.json`. One canonical path function shall derive these locations. Missing required paths, stale paths, and unexpected registered paths shall fail evidence verification.

58. Raw responses shall be write-once immutable bytes with content hashes recorded at write time. Derived tables shall be reproducible from accepted raw responses and shall never be edited manually. Pilot, calibration, confirmatory, pseudo-run, synthetic, and superseded data shall occupy distinct namespaces while using the same production evidence machinery.

59. Every recorded table shall have a codebook row for every column with name, type, permitted values or range, units, causal role, and plain-language definition. Causal role shall be one of Identity, Treatment, Design, Outcome, Post-treatment, and Provenance. Every codebook row shall correspond to a table column. Every value shall satisfy its declared type and domain. Post-treatment fields shall be rejected from primary formulas. Every field declared as execution-constraining shall be consumed by a named integrity check.

60. Pre-confirmatory terminal statuses shall be exactly `QUALIFICATION_FAILURE`, `APPARATUS_FAILURE`, `RESPONSE_LENGTH_INCOMPATIBLE`, `TARGET_RANGE_EXHAUSTED`, `FOCAL_RANGE_EXHAUSTED`, `GRID_RESOLUTION_INSUFFICIENT`, `REFERENCE_POOL_MISMATCH`, `COMPOSED_HEADROOM_FAILURE`, `MEASUREMENT_NOT_ESTABLISHED`, and `MEASUREMENT_EVIDENCE_INSUFFICIENT`.

61. Every failed gate shall emit a terminal report containing model and revision, gate, criterion, threshold, observed value, complete severity curves where applicable, selected and boundary parameters, reference admission table and distances, composed-reference results, truncation and finish-reason summary, verifier status, artifact hashes, producing commit, environment digest, strongest licensed statement, and estimands made unanswerable.

62. One canonical test suite shall establish scientific transcription, architectural identity, provenance, integrity, and lifecycle correctness. It shall test the registered model identities and inference settings; constraints, references, wordings, topics, sequestering, and prompt allocation; verifiers and Gate 1; legal and illegal state transitions; predecessor hash and signature authentication; calibration selection and tie-breakers; complete freeze fields; exact cache identities and counts; primary selection blindness; pseudo-run separation; cross-process writer serialization; dirty-worktree refusal; artifact-state monotonicity; `uv` provenance; durable restoration; Section 27 evidence verification; persistent single-shot masking; persistent single-shot unmasking; statistical estimators and families; terminal reports; and deterministic report reproduction.

63. The end-to-end synthetic lifecycle test shall invoke the actual registered public entrypoints:

```text
qualification
→ pilot
→ regime screen
→ Gate 1
→ Gate 2A
→ Gate 2B
→ freeze
→ synthetic confirmatory cache
→ primary selection
→ confirmatory masking
→ masked analysis
→ single unmask
→ final analysis
```

The synthetic model adapter may replace real inference. The state machine, evidence namespace architecture, evidence writers, integrity checks, primary selector, masking implementation, and analysis entrypoints shall remain the production implementations.

64. The end-to-end test shall prove that the pilot and confirmatory lifecycle use identical production code paths for generation, caching, storage, selection, masking, unmasking, evidence verification, and analysis. It shall attempt a second confirmatory mask creation, a second unmask, a concurrent duplicate cache write, dirty-worktree artifact production, a tampered predecessor PASS record, and a tampered predecessor signature. Every prohibited attempt shall fail before prohibited mutation or key access.

65. The implementation shall finish with one readiness report containing the implementation root, files changed, model repositories and revisions, scientific dependency-isolation result, shared generic infrastructure, canonical public execution interface, state-machine location, evidence-verification location, writer-locking implementation, Git-cleanliness enforcement, `uv` provenance result, Gate 1 implementation result, sequestered-topic access-control result, cache and primary-selection architecture, pseudo-run isolation result, mask single-shot result, unmask single-shot result, predecessor hash-and-signature verification result, durable-restoration result, artifact-state result, canonical test results, complete public-entrypoint synthetic lifecycle trace, authorised E2B carry-over hashes if used, current model-replication states, terminal outcomes reached, hardware-dependent or human-dependent work not executed, and every condition still blocking freeze or confirmation.

66. Registered confirmatory generation shall not run as part of implementation completion. Readiness requires successful qualification of the implementation architecture, the applicable pre-confirmatory checks, complete integrity and provenance tests, persistent custody tests, durable-restoration tests, and the full public-entrypoint synthetic lifecycle.