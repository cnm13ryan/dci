# Decisions requiring approval before the pilot

Every decision must be APPROVED in `approvals.json` against its payload hash before `execute` will run real generation. *design* decisions operationalise the research brief; *proposed* ones are this implementation's choices. Each payload binds the code that implements the decision (docstrings and comments excluded), so editing that code voids the approval. The rationale, revisions and open questions for each decision are in `README.md` §12 and `REMEDIATION_REPORT.md`.

| id | decision | origin | status | payload hash | implementing code |
|---|---|---|---|---|---|
| D01 | **Parameters of the 29 proposed variants**: Concrete targets, counts and minima for the 29 slots the design left open. | proposed | PROPOSED | `750df75fc97b1170` | `library.py`, `verifiers.py` |
| D02 | **The two wording frames and the prompt**: F0 imperative, F1 requirement; A's strings are v8.1 A frames 0/1, B's are historical B wordings 1/0; the carried DCI-1 prompt template with one numbered instruction. | proposed | PROPOSED | `5801a3b53fe7bcb5` | `library.py`, `design.py` |
| D03 | **Text semantics**: Historical alpha-run words for every family; certified sentence segmentation; A folded per word (differs from historical S0 only on U+0130). | proposed | PROPOSED | `404c501ee9208907` | `text.py`, `dci/verifiers/rules.py` |
| D04 | **Outcomes, compliance and vacuity**: Compliant = PASS on a non-empty, untruncated, non-vacuous answer. A completed blank generation (the seam's CHANNEL_INVALID under NO_THINKING) is an EMPTY answer: in n, never compliant, not regenerated. A technical failure is never evidence and stays open for resume, up to max_technical_attempts per row. Literal passes and the reason a pass is excluded are recorded. | proposed | PROPOSED | `faf788812b5ef142` | `verifiers.py`, `outcomes.py`, `scoring.py` |
| D05 | **Stage 1 allocation and pilot topics**: 32 responses per stand-alone cell on one shared set of 32 new topics; task-only 64 per model; 96 pilot topics; the topic bank and its split as reviewed. | proposed | PROPOSED | `8a12b1dfa1ea6db0` | `design.py`, `topics.py` |
| D06 | **Stage 2 refinement rule and stage completeness**: One bounded round, selected only from complete, authenticated Stage 1 evidence: boundary cells ranked by class, then by standardised distance to the boundary; 64 new-topic responses each; at most stage2_max_cells cells. Finalisation needs both stages complete; there is no partial-completion rule. | proposed | PROPOSED | `60cd061a6bf9567e` | `calibration.py`, `evidence.py`, `pipeline.py`, `intervals.py` |
| D07 | **Selecting the two B limits**: Admissible pairs: gap >= b_min_gap; median B-only separation >= b_min_median_separation; that separation in >= b_min_separated_models models; each limit informative in >= b_min_informative_model_frames model-frames. Rank by informative cells, the worse limit, then separation. No admissible pair fails B selection. | proposed | PROPOSED | `3be9d5940f210676` | `calibration.py` |
| D08 | **Selecting the global A count**: Admissible N: p_A inside a_headroom_band in >= a_min_informative_model_frames model-frames across >= a_min_informative_models models. Then maximise configurations with G1 support and an informative A, then headroom, then prefer N=4, then the smaller N. Uninformative-A configurations never count toward feasibility. No admissible N fails A selection; no per-model fallback. | proposed | PROPOSED | `6f2f69abfbaa7201` | `calibration.py`, `references.py` |
| D09 | **Eligibility operationalisation**: Point estimate >= 20% in at least one model-frame, on all stand-alone responses of that cell (Stage 1 + 2); 10% extension reported separately. The OR over eight cells admits candidates whose true rate is below 20% (disclosed). | design | PROPOSED | `7e50ba8f0a5226ca` | `references.py`, `intervals.py` |
| D10 | **Matching operationalisation**: \|p_X - p_A\| <= 0.10 per model-frame on raw compliance; iota uses task-only kappa per model (frame-invariant prompt); undefined iota is unmatched and flagged. Matching is a noisy classification at pilot sample sizes (see D14). | design | PROPOSED | `b4765b94a1dc3727` | `references.py`, `intervals.py` |
| D11 | **Coverage requirements**: Design minima for G1, P1, P2, P3 and the 12-of-16 target; proposed: P3 also needs \|G3\| >= p3_min_g3. | design | PROPOSED | `16cdce2934876bab` | `references.py` |
| D12 | **Model panel, decoding, cap, seeds and backend**: Historical four-model panel and decoding; cap 512 tokens, with any cell truncating above truncation_review_share listed for review; the seed derivation; the vLLM seam source; Python 3.11 for the orchestrator (researcher-approved 2026-10-19) and 3.12 for the vLLM backend (proposed; its pinned wheel is cp312). The execution environment is attested separately and bound by Freeze 1; a bounded, authorised smoke test (never evidence) measures load time, throughput and truncation first. | proposed | PROPOSED | `b21391da5d7e145e` | `runner.py`, `environment.py`, `outcomes.py`, `design.py` |
| D13 | **Object types and hierarchical weights**: Commas and semicolons share the object type punctuation; weights equal over operations, then object types, then parameter variants (so a word with three count variants carries three variant shares). | proposed | PROPOSED | `c98866130ab43754` | `references.py`, `library.py` |
| D14 | **Membership-stability diagnostics**: Topic-cluster bootstrap of the pilot: inclusion frequency per reference, A/B selection and FEASIBLE shares, borderline matches, and feasibility on majority-stable members; a flag when a FEASIBLE verdict's weakest contrast is within near_threshold_margin of the target. Diagnostic only, never a gate: membership stays the point-estimate rule; instability is flagged for review, never auto-corrected. | proposed | PROPOSED | `cae73152de09cf5b` | `stability.py` |

## Changes since the first audit, and what to settle

Every payload hash changed in this revision (each now binds its implementing code), so no earlier approval carries over; none had been given.

### D01 — Parameters of the 29 proposed variants

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

### D05 — Stage 1 allocation and pilot topics

- **Change:** Allocation unchanged. After the re-audit (R1) 88 more questions were rewritten under their ids: the 11 restatements it named, 49 more found by a semantic review of every question against every historical one, one of each of 5 duplicate pairs, and 23 judged too close. The screen adds a rare-word rule; the payload binds both review files. The split does not move.
- **To settle:** Read `TOPIC_REVIEW.md` (every replacement, original and replacement side by side) and approve or ask for changes.

### D06 — Stage 2 refinement rule and stage completeness

- **Change:** REVISED (audit F2). Stage 2 is selected only from complete, authenticated, re-scored Stage 1 evidence and records its hash; planning, executing and finalising Stage 2 refuse when that evidence moves. Finalisation needs both stages complete. There is no partial-completion rule.
- **To settle:** Approve, or specify a final-missingness rule (none is proposed).

### D07 — Selecting the two B limits

- **Change:** REVISED (audit F9). A pair needs median separation >= 0.15, that separation in >= 3 models, and each limit informative in >= 4 of 8 model-frames; otherwise B selection FAILS. Simulated: the threshold does not bind on typical surfaces and fails a shallow surface whose largest true gap is < 0.2.
- **To settle:** Settle the 0.15 threshold, the 3-model consistency rule, and whether a near-ceiling permissive limit (> 0.85) should be admissible (currently it is not).

### D08 — Selecting the global A count

- **Change:** REVISED (audit F3). N is admissible only if p_A is in [0.10, 0.90] in >= 6 of 8 model-frames across >= 3 models; a configuration whose A is outside the band is reported but never counted toward feasibility; no admissible N fails A selection. The floor counterexample no longer reports FEASIBLE.
- **To settle:** Settle the band and the 6-of-8 / 3-model requirement (chosen to match the 12-of-16, 3-model feasibility target).

### D09 — Eligibility operationalisation

- **Change:** Unchanged rule. Disclosed: the OR over eight cells admits a candidate whose true rate is 0.12 everywhere with probability 0.49 at n = 32 (0.07 at n = 96), and 0.15 with 0.82 (0.47), assuming independent responses.
- **To settle:** Approve with the disclosure, or ask for a different rule.

### D10 — Matching operationalisation

- **Change:** Unchanged rule (±0.10 raw). Disclosed: at pilot sample sizes a reference within 0.05 of the edge is misclassified about 40% of the time under every affordable allocation (simulated). D14 reports which memberships are unstable.
- **To settle:** Approve with the disclosure.

### D11 — Coverage requirements

- **Change:** Unchanged rule (design minima of 2). Verified: admission keeps every qualifying reference; a minimum is never a cap. Simulated: the false FEASIBLE verdicts come from ±0.10 matching noise, not from eligibility or A/B selection; on a surface with no truly matched other-operation reference, 87% of pilots report FEASIBLE under the design minimum.
- **To settle:** Decide the rule. The coverage simulation (`COVERAGE_SIMULATION_REVIEW.md`: 15 rules, 12 scenarios, 1,000 paired pilots each) recommends a minimum of 3 for P3 only (P1 and P2 stay at 2). The code still holds the design value 2; approving D11 as it stands approves 2.

### D12 — Model panel, decoding, cap, seeds and backend

- **Change:** REVISED binding. Payload binds the configured models, decoding, seeds, the vLLM seam source, a 2% truncation-review share, the orchestrator and backend Python versions and the source-hash scheme (now identical under Python 3.11, 3.12 and 3.13; re-audit R2). Freeze 1 binds an environment lock attested on the execution host and re-checked live. A bounded, authorised smoke test (`smoke`, at most 96 rows, never evidence) measures load time, throughput and truncation before Freeze 1.
- **To settle:** Python 3.11 for the orchestrator was approved by the researcher on 2026-10-19 (to be recorded in `approvals.json`); every payload and Freeze 1 record it and every command refuses another version. Settle the rest: the cap, the 2% review share, and Python 3.12 for the vLLM backend (its pinned wheel is cp312). Run the smoke test on the intended host first.

### D13 — Object types and hierarchical weights

- **Change:** Unchanged rule. Clarified: parameter variants are weighted individually within an operation-object group, so a word with three count variants carries three variant shares (a G1 of indeed x3, perhaps, instead puts 3/5 on indeed).
- **To settle:** Approve, or add a target-word level to the hierarchy.

### D14 — Membership-stability diagnostics

- **Change:** NEW. Topic-cluster bootstrap of the pilot (200 resamples): inclusion frequency per reference, A/B selection and FEASIBLE shares, borderline matches, a Stage-1-only sensitivity, and feasibility recomputed on majority-stable members. Diagnostic only: membership is never changed by it, and it is not a gate (simulation: it does not reliably separate true from false FEASIBLE).
- **To settle:** Approve as a reported diagnostic; decide how its flags are reviewed before Freeze 2 is accepted. New (R4.5): FEASIBILITY_NEAR_THRESHOLD when the weakest contrast is supported in at most 14 configurations.
