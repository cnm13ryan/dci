# Batch 1 decisions of 2026-10-25, ready to transcribe

**For:** Bryan (the researcher), to fill in `approvals.json`. **Written by:**
the implementing agent (Claude) from Bryan's decisions of 2026-10-25. The
code never writes `approvals.json` and never sets a status; only the
researcher does.

## How to transcribe

1. Copy `docs/batch1/approvals_template.json` to `approvals.json` (in the run
   root `R`, where `freeze-protocol --approvals` reads it). Use the template
   from the commit that will run, because each `payload_hash` binds the
   decision's configuration and implementing code.
2. For each decision below, set `status`, `approved_by`, `approved_on`
   (`2026-10-25` or the day you sign) and `note` as given. Leave
   `payload_hash`, `origin`, `summary` and `title` as generated.
3. Leave `orchestrator_python` at `"3.12"`.
4. D12's approval is conditional (below): record it only after the smoke
   test passes and the environment lock meets its conditions.

The table checks what you transcribe: the payload hashes at the commit this
file was written for. If `approvals_template.json` shows different hashes, the
code changed after this file; use the template's and ask why.

| decision | title | payload_hash (first 16) |
|---|---|---|
| D01 | Parameters of the 29 proposed variants | `1984255921c07e93` |
| D02 | The two wording frames and the prompt | `6b0294a33bb87047` |
| D03 | Text semantics | `f013531202272bc8` |
| D04 | Outcomes, compliance and vacuity | `94c018a1c2dcede3` |
| D05 | Stage 1 allocation and pilot topics | `543834c0bba5d23d` |
| D06 | Stage 2 refinement rule and stage completeness | `c0cb71842c0f3bb8` |
| D07 | Selecting the two B limits | `cc261ae19fd1ad68` |
| D08 | Selecting the global A count | `99a39cd824f437f7` |
| D09 | Eligibility operationalisation | `86db9770310b309f` |
| D10 | Matching operationalisation | `540aaaf0cd3684f1` |
| D11 | Coverage requirements | `32951ab309a6fb20` |
| D12 | Model panel, decoding, cap, seeds and backend | `1017d22295953f4a` |
| D13 | Object types and hierarchical weights | `7f24d04f57e7fdc8` |
| D14 | Membership-stability diagnostics | `da0bb5bb7c0fcd0f` |

## The decisions

| decision | status to set | note to record |
|---|---|---|
| D01 instruction variants | APPROVED | Approved as proposed (PROTOCOL_REVIEW.md D01); `pro.word.the` kept, so the content-word condition does not arise. |
| D02 frames and prompt | APPROVED | Per PROTOCOL_REVIEW.md recommendation. |
| D03 text semantics | APPROVED | Per PROTOCOL_REVIEW.md recommendation; headings and list items count as sentences. |
| D04 outcomes and compliance | APPROVED | Per PROTOCOL_REVIEW.md recommendation, including the CHANNEL_INVALID evidence rule and the retry limit of 3. |
| D05 allocation and topics | APPROVED | After the targeted edits of 2026-10-25 (containment rule on all 67 kept CLOSE pairs, 24 rewritten; 11+-letter word restored in 2 Stage 1 replacements; report generator fixed; fresh second pass on every rewrite; split unchanged). |
| D06 Stage 2 rule | APPROVED | Per PROTOCOL_REVIEW.md recommendation; no partial-completion rule. |
| D07 B selection | APPROVED | B limits above 85% compliance stay inadmissible. |
| D08 A selection | APPROVED | Per PROTOCOL_REVIEW.md recommendation. |
| D09 eligibility | APPROVED | Per PROTOCOL_REVIEW.md recommendation, with its disclosure. |
| D10 matching | APPROVED | ±10-point matching noise accepted and disclosed (text below). |
| D11 coverage | APPROVED | P3 minimum 3 (rule P3k3); P1, P2, G1 minima and the 12-of-16 target unchanged. |
| D12 models, decoding, backend | APPROVED (conditional) | Conditions below; record only once they are met. |
| D13 weights | APPROVED | Per PROTOCOL_REVIEW.md recommendation, with its disclosure. |
| D14 stability diagnostics | APPROVED | Diagnostics, not gates; Freeze 2 flags are read by the rule below, blocking by default. |

## What each decision rests on

**D01: the compliance evidence.** There is none. No model has generated
anything in Batch 1, so no instruction's compliance rate is known. The
evidence behind D01 is constructive: every variant has a passing and a
failing example checked by its verifier (`validate-verifiers`), and a 60-120
word example that also satisfies B for every compatible B limit (305 of 305
cells, confirmed by the auditor's independent checker). PROTOCOL_REVIEW.md
recommends approving, with an *optional* swap of "do not use *the*"; following
the recommendation keeps it. Its difficulty is handled by eligibility (D09):
if models almost never manage it, it is ineligible and drops out.

**D05: what changed.** See `TOPIC_REVIEW.md` §3c and the containment table in
`topic_screen_report.md`.

- **(a)** The rule: a pair is a restatement when a good answer to either
  question would largely answer the other, in either direction. Two judges
  applied it to all 67 kept CLOSE pairs, each blind to the other: the author
  and an independent model reviewer. The author judged 23 restatements, the
  reviewer 10, and they agreed on 9. All 24 in the union were rewritten. Of
  the five you named, the reviewer upheld only music-04; the author judged
  all five restatements.
- **(b)** `b1-history-28` now uses "professional" and `b1-technology-20`
  "approximate". Stage 1 is back to 3 of 32 questions with an 11+-letter
  word, mean longest word 8.06, with letters b and z and the opening words
  unchanged.
- **(c)** The §3 tables are generated (`report.topic_replacements`). They
  reproduce all 88 earlier rows exactly, except work-and-organisations-36,
  which now cites its partner as it read at review time.
- **(d)** A fresh reviewer read both full lists and judged the 26 new
  questions. It found one restatement (menthol and the chili-heat question)
  and one false premise; both were rewritten and cleared by another fresh
  reviewer. Before review, the author's own checks replaced 19 drafts: 16
  were near-paraphrases of historical questions (for example a metronome
  question that a v19 task asks) and 3 were flagged only by the word-overlap
  screen. 3 more candidates were rejected before being drafted. All are
  listed in `TOPIC_REVIEW.md` §2a; an earlier count of 13 was wrong.
- **(e)** The split is unchanged: the same 32, 64 and 480 ids (test).

**D11.** COVERAGE_SIMULATION_REVIEW.md §8 recommends exactly this rule (P3k3)
and keeps the 12-of-16 target with the P1, P2 and G1 minima, so the rule
meets the coverage target as defined.

The figures below are recomputed from `coverage_simulation.json` (1,000
simulated pilots per scenario). Each rule is judged against its own
noise-free truth. They correct the ones first written here, which the third
audit found described only part of the picture (C2).

| scenario | true verdict, minimum 2 → 3 | pilots reporting FEASIBLE, minimum 2 → 3 |
|---|---|---|
| moderate, model differences, edge crowded | FEASIBLE → FEASIBLE | 99-100% → 98-99% |
| boundary cluster, frame differences | FEASIBLE → FEASIBLE | 98-100% → 96-98% |
| strong paraphrase sensitivity | FEASIBLE → FEASIBLE | 90% → 88% |
| single operation coverage | FEASIBLE → FEASIBLE | 98% → 85% |
| strong model sensitivity | FEASIBLE → FEASIBLE | 86% → 53% |
| graded coverage | FEASIBLE → **INFEASIBLE** | 89% → 40% (now false FEASIBLE) |
| low followability | FEASIBLE → **INFEASIBLE** | 69% → 47% (now false FEASIBLE) |
| graded coverage, sparse | INFEASIBLE → INFEASIBLE | 59% → 14% (false FEASIBLE) |
| other operation harder | INFEASIBLE → INFEASIBLE | 87% → 23% (false FEASIBLE) |

What this means:

- **False FEASIBLE.** Where both rules call the study infeasible, the
  minimum of 3 cuts false FEASIBLE from 59% to 14% and from 87% to 23%. That
  is the "73% → 18%" quoted before, which is the mean of those two rows. In
  the two scenarios that only the minimum of 3 calls infeasible, it still
  reports FEASIBLE 40% and 47% of the time.
- **False INFEASIBLE.** It rises by 0-3 points in the typical scenarios
  (moderate, model, edge, boundary, frame, paraphrase), not "about 1 point"
  everywhere. It rises by 13 points with coverage from a single operation and
  by 33 points when models differ strongly.

Whether the minimum of 3 is still your rule, given these figures, is your
decision. The implementing agent still recommends it: it is the only rule
that substantially cuts false FEASIBLE, and its cost falls where models or
operations differ strongly, which the Stage-1-only and stability reports
show.

One caveat: the earlier precision study (`calibration_precision.json`,
CALIBRATION_PRECISION_REVIEW.md) was run under the design minimum of 2, so
its D07 and D14 numbers do not use this rule.

## D10: the disclosure text

> Difficulty matching (D10) classifies a reference as matched to A when its
> stand-alone compliance is within 10 percentage points of A's, in each
> model-frame, on the pilot's sample. At these sample sizes the
> classification is noisy near its edge: a reference within 2 points of the
> ±10 boundary is misclassified about 45% of the time, and the matched
> populations overlap the populations that exact rates would give only about
> half the time (Jaccard ≈ 0.5; CALIBRATION_PRECISION_REVIEW.md §5,
> COVERAGE_SIMULATION_REVIEW.md §6.2 and §6.4). This noise is the main source
> of false FEASIBLE verdicts, which the P3 minimum of 3 (D11) reduces but does
> not remove. The researcher accepted the rule as prespecified rather than
> change it after seeing data. Batch 2 should therefore report each contrast
> together with its population's borderline matches and the D14 stability
> diagnostics.

## D12: the wording and the conditions

**Rationale (as now in the D12 payload).** Python 3.12 for the orchestrator
and the vLLM backend. The CUDA vllm 0.15.1 wheel is cp38-abi3, so the wheel
does not force a Python version; 3.12 is vLLM's Docker default and native on
Lambda's GPU Base 24.04. Execution requirements: vllm 0.15.1 and torch
2.9.1+cu129 on 2x H100 SXM with driver >= 575.51.03. One worker per GPU, with
tensor parallelism as configured (1). Batch invariance off, enforced: the
runner passes no inherited `VLLM_*` setting to the backend. Amended the same
day, after the first pilot run was stopped for low GPU use
(`PILOT_ABORT_2026-10-25.md`): 512 requests per generate call (was 64), CUDA
graphs off (now explicit in the payload).

**Disclosure.** A row regenerated in a fresh process is byte-identical to the
first generation about 97% of the time at these settings (95.5% at the
earlier chunk 64), not always. vLLM is not batch-invariant here. The evidence
is the stored records bound by Freeze 2.

**Conditions, checked before you record APPROVED:**

| condition | how it is checked |
|---|---|
| Python 3.12, vllm 0.15.1, torch 2.9.1+cu129 (CUDA 12.9) | `bootstrap.sh` prints `2.9.1+cu129 12.9 True 0.15.1`; `attest-environment` refuses any other build |
| 2x H100 SXM (`NVIDIA H100 80GB HBM3`, compute capability 9.0) | bound in the lock (model, count, capability, memory); a lock that differs is refused, and `execute` re-checks it live |
| driver >= 575.51.03 | `preflight.sh`; `attest-environment` refuses a lower driver. The driver build is recorded, not bound |
| smoke test passes: no crashes, blank answers handled as expected, at most 1 cap hit per model | computed by the code (third audit C3). Run `smoke ... --environment-lock environment_lock.json`; `smoke_report.json` then has `d12_pass` per model and overall, and the command exits 0 only when it is true. Per model, a pass needs: every planned row returned; exit 0 or 1; not blocked; no TECHNICAL outcome, so any blank answer was classed EMPTY; and at most one answer stopped by the 512-token cap. Overall, the live backend must also equal the attested lock's identity and meet these requirements live |

These requirements are in the D12 payload (`EXECUTION_REQUIREMENTS`), so
approving D12 approves them. They are enforced when the lock is made, when
Freeze 1 is built, and live at every `execute`, which also refuses ROCm GPU
selection on a CUDA backend.

The provisional smoke runs on 2026-10-25 (`smoke-2026-10-25b` and the two
per-GPU runs) met every condition by hand-check, but they predate the
computed `d12_pass`. Record D12 against a re-run that reports
`d12_pass: true`.

**The lock decision (implemented).** The lock binds the software identity and
the GPU class: model, count, compute capability and memory. It records the
hostname, GPU UUIDs, driver build and kernel without binding them.

## D14: how Freeze 2 flags are read (draft for your approval)

**The rule: a flag blocks Batch 2 unless this table says otherwise, and so
does any flag not listed.** "Blocks" means Batch 2 is not designed or run on
this Freeze 2 until you have recorded, in writing, what you decided about the
flag. A block never edits Freeze 2 or re-runs the pilot: that would choose
after seeing data.

| flag or report item | what it means | action |
|---|---|---|
| status `B_SELECTION_FAILED`, `A_HEADROOM_INADEQUATE` | no admissible B pair or A count | **block**; Freeze 2 is already `REVISION_REQUIRED`, so the design must be revised |
| verdict `INFEASIBLE_REVISION_REQUIRED`, `A_COVERAGE_INADEQUATE` | coverage target not met | **block** (as above) |
| `A cells incomplete` | A cells missing data | **block**; resume the stage (finalisation refuses incomplete stages) |
| `FEASIBILITY_RESTS_ON_UNSTABLE_MEMBERS` | not feasible on majority-stable members | **block** |
| `FEASIBILITY_UNSTABLE` | FEASIBLE in too few resamples | **block** |
| near threshold (`near_threshold` in Freeze 2) | how many configurations support the weakest contrast, and whether that is within 2 of 12 | **record only**: written into Freeze 2 and reported with Batch 2; not a flag and never blocks (your decision of 2026-10-25) |
| Stage-1-only sensitivity disagrees with the verdict | the verdict depends on Stage 2 topics | **block** |
| `MEMBERSHIP_UNSTABLE` | some configuration has references in the unstable inclusion band | **proceed with disclosure**: Batch 2 reports each population's effective number of references and a leave-one-reference-out check (D13). It fires on almost any real pilot, so blocking on it would block every outcome |
| `truncation_review` cells (truncation > 2%) | some cells hit the 512-token cap often | **block until reviewed**: read the listed cells' truncated answers and record whether the cap changed what compliance means there |
| any other flag | | **block** |

**Near threshold: recorded, not flagged (your decision of 2026-10-25).**
Freeze 2 no longer raises `FEASIBILITY_NEAR_THRESHOLD`. Instead it records,
under `near_threshold`, the support for P1-P3, the weakest, the target (12),
the margin (2) and whether the weakest is within it. Nothing waits on it.

For reading it later: under the P3 minimum of 3, a weakest contrast within 2
of the target occurs on 30-96% of correct FEASIBLE verdicts in the simulation
(53-67% in typical scenarios; third audit C2). So being near the threshold is
common and is not by itself evidence of a false FEASIBLE.
