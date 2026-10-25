# Decisions requiring approval before the pilot

Every decision must be APPROVED in `approvals.json` against its payload hash before `execute` will run real generation. *design* decisions operationalise the research brief; *proposed* ones are this implementation's choices. Each payload binds the code that implements the decision (docstrings and comments excluded), so editing that code voids the approval. The rationale, revisions and open questions for each decision are in `README.md` §12 and `REMEDIATION_REPORT.md`.

| id | decision | origin | status | payload hash | implementing code |
|---|---|---|---|---|---|
| D01 | **Parameters of the 139 proposed variants**: Concrete targets, counts and minima for the 139 slots the design left open (library v2: the v1 slots plus the R1 additions). | proposed | PROPOSED | `8be7ebefa3c301f0` | `library.py`, `verifiers.py` |
| D02 | **The two wording frames and the prompt**: F0 imperative, F1 requirement; A's strings are v8.1 A frames 0/1, B's are historical B wordings 1/0; the carried DCI-1 prompt template with one numbered instruction. | proposed | PROPOSED | `6e647ef48ddd0cdc` | `library.py`, `design.py` |
| D03 | **Text semantics**: Historical alpha-run words for every family; certified sentence segmentation; A folded per word (differs from historical S0 only on U+0130). | proposed | PROPOSED | `f013531202272bc8` | `text.py`, `dci/verifiers/rules.py` |
| D04 | **Outcomes, compliance and vacuity**: Compliant = PASS on a non-empty, untruncated, non-vacuous answer. A completed blank generation (the seam's CHANNEL_INVALID under NO_THINKING) is an EMPTY answer: in n, never compliant, not regenerated. A technical failure is never evidence and stays open for resume, up to max_technical_attempts per row. Literal passes and the reason a pass is excluded are recorded. | proposed | PROPOSED | `77391ef848920b9e` | `verifiers.py`, `outcomes.py`, `scoring.py` |
| D05 | **Topic bank v3 and its split**: The 144 topics of bank v3, written fresh for v2.1 (distinct from bank v1 with its 480 reserved topics, and from bank v2, whose topics the v2 run of 2026-10-26 measured), in 12 areas, split by a fixed seed into T1 (48 topics, Stage A screening; one response per stand-alone and task-only cell) and T2 (96 topics, Stage C membership); none reserved. Screened against the historical banks and every earlier Batch 1 bank, by word overlap and a blind semantic review; bank v1's 480 reserved topics stay unused, for the confirmatory study (30 of bank v3's 79 CLOSE pairs are close to a reserved topic: same narrow subject, a different question; none is a restatement). | proposed | PROPOSED | `1b59a20a1a4776c4` | `design.py`, `topics.py` |
| D06 | **Stages A-D, the T1 forecast, and what T2 measures**: Stage A measures every reference, A x 4/5/6, B 8 and 10 and the task alone on T1. Stage B draws each T1 cell from its Beta posterior (forecast_draws draws, forecast_seed) and applies D08-D11, with the fixed-A (D08) and fixed-B (R4) gates, to every draw. It reports, per contrast, P(feasible), coverage ignoring the gates, coverage given the gates pass, and P(the gates pass), and names what would have limited the run: the library (a contrast's coverage, given the gates pass, reaches the target in < forecast_min_feasible of the draws) and/or the fixed A or B (the gates pass in < forecast_min_feasible of the draws). No early stop (the researcher's decision of 2026-10-26): the forecast is reported, never acted on, and Stage C always runs. Stage C measures every reference in the library, plus A x 6, B 8 and 10 and the task alone, one response per T2 topic. T2 alone decides eligibility, matching and membership; T1 never enters them. No C' top-up. Both stages must be complete (no partial-completion rule). Budget: the Stage C plan is refused if Stage A's planned rows plus it exceed max_total_rows. There is no run-time guard: technical retries (at most max_technical_attempts per row), rows a crashed or blocked backend never delivered, and the smoke test (its own root) are not charged, and are reported in calibration.json's accounting. | proposed | PROPOSED | `0a89b11eae5986cc` | `calibration.py`, `evidence.py`, `pipeline.py`, `intervals.py`, `revision.py`, `runner.py` |
| D07 | **B fixed at 8 and 10, checked on T2**: B is fixed (R4), not selected. On T2 each limit must be informative (B-only compliance inside b_informative_band) in >= b_min_informative_model_frames model-frames, or the verdict is B_NOT_INFORMATIVE. | proposed | PROPOSED | `cba31502263f1ab2` | `calibration.py`, `revision.py` |
| D08 | **A fixed at however x 6, checked on T2**: A is fixed (R3), not selected; A x 4 and x 5 are measured on T1 as diagnostics only. On T2, A must be informative (p_A inside a_headroom_band) in >= a_min_informative_model_frames model-frames across >= a_min_informative_models models, or the verdict is A_NOT_ADMISSIBLE. Uninformative-A configurations never count toward feasibility; a G1 count below the target is flagged A_COVERAGE_INADEQUATE. | proposed | PROPOSED | `8b26ee0565d6253c` | `calibration.py`, `references.py`, `revision.py` |
| D09 | **Eligibility operationalisation**: Point estimate >= 20% in at least one model-frame, on the T2 responses of that cell only; 10% extension reported separately. The OR over eight cells admits candidates whose true rate is below 20% (disclosed). | design | PROPOSED | `693a541514b53b19` | `references.py`, `intervals.py` |
| D10 | **Matching operationalisation**: \|p_X - p_A\| <= 0.10 per model-frame on raw T2 compliance, in exact arithmetic (primary, deciding). Reported beside it, never deciding (R5): posterior P(match) per reference and model-frame, and coverage under +/-0.15, +/-0.20, confident matching (Newcombe interval inside +/-0.10) and iota matching. | design | PROPOSED | `8aea13eb4c32b275` | `references.py`, `intervals.py`, `revision.py` |
| D11 | **Coverage requirements**: Design minima for G1 (3 distinct words), P1 (G2 adds 2) and P2 (G3 adds 2 other-object references). P3 is stricter than the design (the researcher's decision of 2026-10-25): G5 adds 3 other-operation references, not 2, and \|G3\| >= p3_min_g3 (3). Feasibility needs 12 of 16 configurations, 3 models and both B limits (unchanged). Pools are eligible references logically compatible with the configuration's B limit. Stage B's forecast uses exactly these rules. | design | PROPOSED | `175eff23a2f825d8` | `references.py`, `revision.py`, `compatibility.py` |
| D12 | **Model panel, decoding, cap, seeds and backend**: Historical four-model panel and decoding; cap 512 tokens, with any cell truncating above truncation_review_share listed for review; the seed derivation; the vLLM seam source; Python 3.12 for the orchestrator and the vLLM backend (the CUDA vllm 0.15.1 wheel is cp38-abi3; 3.12 is vLLM's Docker default and native on GPU Base 24.04); the execution requirements (vllm 0.15.1, torch 2.9.1+cu129, 2x H100 SXM, driver >= 575.51.03), one worker per GPU, TP as configured. The execution environment is attested on the host, checked against the requirements and bound by Freeze 1; a bounded, authorised smoke test (never evidence) measures load time, throughput and truncation first. | proposed | PROPOSED | `65989d064bb42931` | `runner.py`, `environment.py`, `outcomes.py`, `design.py` |
| D13 | **Object types and hierarchical weights**: Object types as in v1 plus library v2's (numerals, sentence and paragraph ladders, positional); weights equal over operations, then object types, then, inside an exact-word-count group, equal over target words and then over a word's count variants (R10). | proposed | PROPOSED | `a8f14ab1c98e1ac7` | `references.py`, `library.py` |
| D14 | **Membership-stability diagnostics, their review, and T1-T2 agreement**: Topic-cluster bootstrap on T2: inclusion frequency, FEASIBLE share, borderline matches, feasibility on majority-stable members; a near-threshold record; a truncation review of cells above truncation_review_share with >= truncation_review_min_rows truncated rows (R11). Also reported: T1-versus-T2 agreement (eligibility, matching, forecast against verdict). Review rule (the researcher's of 2026-10-25, DECISIONS_2026-10-25.md): every Freeze 2 flag blocks Batch 2 until the researcher reviews it, including FEASIBILITY_UNSTABLE and any truncation-review cell; only MEMBERSHIP_UNSTABLE proceeds, with disclosure. Nothing is auto-corrected and no threshold is changed in response to a result. | proposed | PROPOSED | `3fa5524377c7a9b5` | `stability.py`, `revision.py` |

## Changes from v1, and what an approval accepts

No v1 or v2 approval carries over: every payload binds the v2.1 code.

### D01 — Parameters of the 139 proposed variants

- **Change:** Library v2 (R1): v1's slots plus 110 additions.
- **To settle:** Accept the parameters listed in `library_review.md`.

### D02 — The two wording frames and the prompt

- **Change:** Frames and prompt as v1; target words are quoted (R2).
- **To settle:** Accept the quoted renderings (every rendering is in the payload).

### D03 — Text semantics

- **Change:** Unchanged.
- **To settle:** As v1.

### D04 — Outcomes, compliance and vacuity

- **Change:** Unchanged rules; three new verifiers (numerals, positional word, final question).
- **To settle:** As v1.

### D05 — Topic bank v3 and its split

- **Change:** Bank v3: 144 topics written fresh for v2.1 (T1 48 / T2 96, none reserved), screened against every earlier bank, including bank v2, which the v2 run measured.
- **To settle:** Accept bank v3 and its reviews (`topic_screen_report.md`).

### D06 — Stages A-D, the T1 forecast, and what T2 measures

- **Change:** Stages A-D; every reference measured on T2 (v2.1, audit B1); no C' top-up (R7 option b); budget 192,000 rows.
- **To settle:** Accept the three departures from R7(a): C' dropped, the budget, and carrying all 161 instead of at most 110.

### D07 — B fixed at 8 and 10, checked on T2

- **Change:** B fixed at 8 and 10 (R4); checked on T2, not selected.
- **To settle:** Accept B_NOT_INFORMATIVE as the outcome if a limit fails.

### D08 — A fixed at however x 6, checked on T2

- **Change:** A fixed at however x 6 (R3); A x 4 and x 5 diagnostics only.
- **To settle:** Accept A_NOT_ADMISSIBLE as the outcome if A fails on T2.

### D09 — Eligibility operationalisation

- **Change:** T2 responses only (R7).
- **To settle:** As v1 otherwise.

### D10 — Matching operationalisation

- **Change:** Primary rule unchanged; R5(a) reports added, never deciding. Confident matching is expected near zero at n = 96 (the interval's half-width is about 0.14).
- **To settle:** Accept the reports as labelled sensitivities.

### D11 — Coverage requirements

- **Change:** Unchanged minima and target; P3 needs 3 additional other-operation references, stricter than the design's 2 (the researcher's decision of 2026-10-25); the forecast uses them.
- **To settle:** As approved for v1 and v2.

### D12 — Model panel, decoding, cap, seeds and backend

- **Change:** Seed domain dci.batch1:gen:v2.1; otherwise as re-approved for 0cde3b9 (R13).
- **To settle:** Re-approve after the v2.1 smoke test.

### D13 — Object types and hierarchical weights

- **Change:** Word-then-count weights (R10): equal over target words, then over a word's count variants.
- **To settle:** Accept R10's weights.

### D14 — Membership-stability diagnostics, their review, and T1-T2 agreement

- **Change:** T2 bootstrap; truncation review needs >= 2 rows (R11); T1-versus-T2 agreement reported; the review rule of 2026-10-25 is stated in the decision itself.
- **To settle:** Every Freeze 2 flag blocks Batch 2 until you review it; only MEMBERSHIP_UNSTABLE proceeds with disclosure.
