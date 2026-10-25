# Decisions requiring approval before the pilot

Every decision must be APPROVED in `approvals.json` against its payload hash before `execute` will run real generation. *design* decisions operationalise the research brief; *proposed* ones are this implementation's choices. Each payload binds the code that implements the decision (docstrings and comments excluded), so editing that code voids the approval. The rationale, revisions and open questions for each decision are in `README.md` §12 and `REMEDIATION_REPORT.md`.

| id | decision | origin | status | payload hash | implementing code |
|---|---|---|---|---|---|
| D01 | **Parameters of the 139 proposed variants**: Concrete targets, counts and minima for the 139 slots the design left open (library v2: the v1 slots plus the R1 additions). | proposed | PROPOSED | `8be7ebefa3c301f0` | `library.py`, `verifiers.py` |
| D02 | **The two wording frames and the prompt**: F0 imperative, F1 requirement; A's strings are v8.1 A frames 0/1, B's are historical B wordings 1/0; the carried DCI-1 prompt template with one numbered instruction. | proposed | PROPOSED | `6e647ef48ddd0cdc` | `library.py`, `design.py` |
| D03 | **Text semantics**: Historical alpha-run words for every family; certified sentence segmentation; A folded per word (differs from historical S0 only on U+0130). | proposed | PROPOSED | `f013531202272bc8` | `text.py`, `dci/verifiers/rules.py` |
| D04 | **Outcomes, compliance and vacuity**: Compliant = PASS on a non-empty, untruncated, non-vacuous answer. A completed blank generation (the seam's CHANNEL_INVALID under NO_THINKING) is an EMPTY answer: in n, never compliant, not regenerated. A technical failure is never evidence and stays open for resume, up to max_technical_attempts per row. Literal passes and the reason a pass is excluded are recorded. | proposed | PROPOSED | `77391ef848920b9e` | `verifiers.py`, `outcomes.py`, `scoring.py` |
| D05 | **Topic bank v2 and its split**: 144 fresh topics in 12 areas, split by a fixed seed into T1 (48 topics, Stage A screening; one response per stand-alone and task-only cell) and T2 (96 topics, Stage C membership); none reserved. Screened against the historical banks and bank v1; bank v1's 480 reserved topics stay unused, for the confirmatory study. | proposed | PROPOSED | `f7c83feda84ac7c4` | `design.py`, `topics.py` |
| D06 | **Stages A-D, forecast, early stop and what T2 measures**: Stage A measures every reference, A x 4/5/6, B 8 and 10 and the task alone on T1. Stage B draws each T1 cell from its Beta posterior and applies D08-D11 with the fixed-A and fixed-B gates; it stops before T2 if P(feasible) < forecast_min_feasible for any contrast. Stage C measures every reference in the library, plus A x 6, B 8 and 10 and the task alone, one response per T2 topic. T2 alone decides eligibility, matching and membership; T1 never enters them. No C' top-up. Both stages must be complete (no partial-completion rule); at most max_total_rows responses. | proposed | PROPOSED | `cf0c6c96beafe2ad` | `calibration.py`, `evidence.py`, `pipeline.py`, `intervals.py` |
| D07 | **B fixed at 8 and 10, checked on T2**: B is fixed (R4), not selected. On T2 each limit must be informative (B-only compliance inside b_informative_band) in >= b_min_informative_model_frames model-frames, or the verdict is B_NOT_INFORMATIVE. | proposed | PROPOSED | `aab11eb22e616519` | `calibration.py` |
| D08 | **A fixed at however x 6, checked on T2**: A is fixed (R3), not selected; A x 4 and x 5 are measured on T1 as diagnostics only. On T2, A must be informative (p_A inside a_headroom_band) in >= a_min_informative_model_frames model-frames across >= a_min_informative_models models, or the verdict is A_NOT_ADMISSIBLE. Uninformative-A configurations never count toward feasibility; a G1 count below the target is flagged A_COVERAGE_INADEQUATE. | proposed | PROPOSED | `7b2dc3a8d51c55d1` | `calibration.py`, `references.py` |
| D09 | **Eligibility operationalisation**: Point estimate >= 20% in at least one model-frame, on the T2 responses of that cell only; 10% extension reported separately. The OR over eight cells admits candidates whose true rate is below 20% (disclosed). | design | PROPOSED | `693a541514b53b19` | `references.py`, `intervals.py` |
| D10 | **Matching operationalisation**: \|p_X - p_A\| <= 0.10 per model-frame on raw T2 compliance, in exact arithmetic (primary, deciding). Reported beside it, never deciding (R5): posterior P(match) per reference and model-frame, and coverage under +/-0.15, +/-0.20, confident matching (Newcombe interval inside +/-0.10) and iota matching. | design | PROPOSED | `0c3fe100d51b8e9b` | `references.py`, `intervals.py` |
| D11 | **Coverage requirements**: Design minima for G1, P1 and P2; P3 needs 3 additional other-operation references and \|G3\| >= p3_min_g3; feasibility needs 12 of 16 configurations, 3 models and both B limits (unchanged). Pools are eligible references logically compatible with the configuration's B limit. Stage B's forecast uses exactly these rules. | design | PROPOSED | `b4f7d95a4ad24ef4` | `references.py` |
| D12 | **Model panel, decoding, cap, seeds and backend**: Historical four-model panel and decoding; cap 512 tokens, with any cell truncating above truncation_review_share listed for review; the seed derivation; the vLLM seam source; Python 3.12 for the orchestrator and the vLLM backend (the CUDA vllm 0.15.1 wheel is cp38-abi3; 3.12 is vLLM's Docker default and native on GPU Base 24.04); the execution requirements (vllm 0.15.1, torch 2.9.1+cu129, 2x H100 SXM, driver >= 575.51.03), one worker per GPU, TP as configured. The execution environment is attested on the host, checked against the requirements and bound by Freeze 1; a bounded, authorised smoke test (never evidence) measures load time, throughput and truncation first. | proposed | PROPOSED | `d8efa6f0b569b89b` | `runner.py`, `environment.py`, `outcomes.py`, `design.py` |
| D13 | **Object types and hierarchical weights**: Object types as in v1 plus library v2's (numerals, sentence and paragraph ladders, positional); weights equal over operations, then object types, then, inside an exact-word-count group, equal over target words and then over a word's count variants (R10). | proposed | PROPOSED | `a8f14ab1c98e1ac7` | `references.py`, `library.py` |
| D14 | **Membership-stability diagnostics and T1-T2 agreement**: Topic-cluster bootstrap on T2: inclusion frequency, FEASIBLE share, borderline matches, feasibility on majority-stable members; a near-threshold record; a truncation review of cells above truncation_review_share with >= truncation_review_min_rows truncated rows (R11). Also reported: T1-versus-T2 agreement (eligibility, matching, forecast against verdict), a winner's-curse diagnostic. Diagnostics, never automatic corrections. | proposed | PROPOSED | `f55f14e471d64903` | `stability.py` |

## Changes since the first audit, and what to settle

Every payload hash changed in this revision (each now binds its implementing code), so no earlier approval carries over; none had been given.

### D01 — Parameters of the 139 proposed variants

- **Change:** Unchanged rule; payload now also binds `library.py` code.
- **To settle:** Approve the 29 variants, or swap `pro.word.the` for a content word. The two chain variants are likely very hard; eligibility handles that.

### D02 — The two wording frames and the prompt

- **Change:** Unchanged wordings; payload now also binds the frames list and the prompt templates (moved from D12).
- **To settle:** Optional cosmetic change: B's F1 says 'the answer' where every other F1 says 'your answer'. Not changed here.

### D03 — Text semantics

- **Change:** Unchanged rule; binds `text.py` and `dci/verifiers/rules.py`. Each scored row now records `structure_lines` (markdown heading, list and quote lines), a diagnostic only.
- **To settle:** Approve, knowing headings and list items count as sentences.

### D04 — Outcomes, compliance and vacuity

- **Change:** REVISED implementation (audit F1). Outcome classes: VALID, EMPTY (a completed blank generation; the seam's CHANNEL_INVALID under NO_THINKING when the row shows it) and TECHNICAL (never evidence, kept in `rejected.jsonl`, retried on resume). EMPTY is in every denominator and never complies, and is not regenerated. A PASS that is not compliance records why (vacuous, truncated, empty), so literal and primary compliance are both recoverable. The primary definition is unchanged.
- **To settle:** Approve the outcome classes and the CHANNEL_INVALID evidence rule. `refusal_like` is a phrase-list diagnostic only. New after the re-audit (R4.4): a row whose own outcome is TECHNICAL 3 times (`max_technical_attempts`) is not sent again and the stage stays incomplete.

### D05 — Topic bank v2 and its split

- **Change:** Allocation unchanged. After the re-audit (R1) 88 more questions were rewritten under their ids: the 11 restatements it named, 49 more found by a semantic review of every question against every historical one, one of each of 5 duplicate pairs, and 23 judged too close. The screen adds a rare-word rule; the payload binds both review files. The split does not move.
- **To settle:** Read `TOPIC_REVIEW.md` (every replacement, original and replacement side by side) and approve or ask for changes.

### D06 — Stages A-D, forecast, early stop and what T2 measures

- **Change:** REVISED (audit F2). Stage 2 is selected only from complete, authenticated, re-scored Stage 1 evidence and records its hash; planning, executing and finalising Stage 2 refuse when that evidence moves. Finalisation needs both stages complete. There is no partial-completion rule.
- **To settle:** Approve, or specify a final-missingness rule (none is proposed).

### D07 — B fixed at 8 and 10, checked on T2

- **Change:** REVISED (audit F9). A pair needs median separation >= 0.15, that separation in >= 3 models, and each limit informative in >= 4 of 8 model-frames; otherwise B selection FAILS. Simulated: the threshold does not bind on typical surfaces and fails a shallow surface whose largest true gap is < 0.2.
- **To settle:** Settle the 0.15 threshold, the 3-model consistency rule, and whether a near-ceiling permissive limit (> 0.85) should be admissible (currently it is not).

### D08 — A fixed at however x 6, checked on T2

- **Change:** REVISED (audit F3). N is admissible only if p_A is in [0.10, 0.90] in >= 6 of 8 model-frames across >= 3 models; a configuration whose A is outside the band is reported but never counted toward feasibility; no admissible N fails A selection. The floor counterexample no longer reports FEASIBLE.
- **To settle:** Settle the band and the 6-of-8 / 3-model requirement (chosen to match the 12-of-16, 3-model feasibility target).

### D09 — Eligibility operationalisation

- **Change:** Unchanged rule. Disclosed: the OR over eight cells admits a candidate whose true rate is 0.12 everywhere with probability 0.49 at n = 32 (0.07 at n = 96), and 0.15 with 0.82 (0.47), assuming independent responses.
- **To settle:** Approve with the disclosure, or ask for a different rule.

### D10 — Matching operationalisation

- **Change:** Unchanged rule (±0.10 raw). Disclosed: at pilot sample sizes a reference within 0.05 of the edge is misclassified about 40% of the time under every affordable allocation (simulated). D14 reports which memberships are unstable.
- **To settle:** Approve with the disclosure.

### D11 — Coverage requirements

- **Change:** REVISED by the researcher's decision of 2026-10-25: P3 needs G5 to add at least 3 references of another operation (rule P3k3; the design value was 2). P1, P2 and G1 minima and the 12-of-16 target are unchanged. Verified: admission keeps every qualifying reference; a minimum is never a cap. Simulated: the false FEASIBLE verdicts come from ±0.10 matching noise, not from eligibility or A/B selection.
- **To settle:** Approve the minimum of 3 knowing its simulated cost (`DECISIONS_2026-10-25.md`, D11): false FEASIBLE falls from 87% to 23% and 59% to 14% where both rules are infeasible, but is 40-47% in the two scenarios the minimum of 3 makes infeasible; false INFEASIBLE rises by 0-3 points in typical scenarios and by 13-33 where models or operations differ strongly.

### D12 — Model panel, decoding, cap, seeds and backend

- **Change:** REVISED binding. Payload binds the configured models, decoding, seeds, the vLLM seam source, a 2% truncation-review share, the orchestrator and backend Python versions and the source-hash scheme (now identical under Python 3.11, 3.12 and 3.13; re-audit R2). Freeze 1 binds an environment lock attested on the execution host and re-checked live. A bounded, authorised smoke test (`smoke`, at most 96 rows, never evidence) measures load time, throughput and truncation before Freeze 1.
- **To settle:** Python 3.12 for the orchestrator and the vLLM backend (the researcher's decision of 2026-10-25, replacing 3.11); every payload and Freeze 1 record it and every command refuses another version. The approval is conditional on the execution requirements (vllm 0.15.1, torch 2.9.1+cu129, 2x H100 SXM, driver >= 575.51.03), which the lock enforces, and on a smoke test whose computed `d12_pass` is true against the attested lock (`DECISIONS_2026-10-25.md`, D12).

### D13 — Object types and hierarchical weights

- **Change:** Unchanged rule. Clarified: parameter variants are weighted individually within an operation-object group, so a word with three count variants carries three variant shares (a G1 of indeed x3, perhaps, instead puts 3/5 on indeed).
- **To settle:** Approve, or add a target-word level to the hierarchy.

### D14 — Membership-stability diagnostics and T1-T2 agreement

- **Change:** NEW. Topic-cluster bootstrap of the pilot (200 resamples): inclusion frequency per reference, A/B selection and FEASIBLE shares, borderline matches, a Stage-1-only sensitivity, and feasibility recomputed on majority-stable members. Diagnostic only: membership is never changed by it, and it is not a gate (simulation: it does not reliably separate true from false FEASIBLE).
- **To settle:** Approve as a reported diagnostic; decide how its flags are reviewed before Freeze 2 is accepted (`DECISIONS_2026-10-25.md`, D14). Freeze 2 records how many configurations support the weakest contrast and whether that is within 2 of the target; by the researcher's decision of 2026-10-25 this is a record, not a flag.
