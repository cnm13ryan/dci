# Batch 1 researcher review: start here

**Purpose:** everything you need to approve, revise or defer the Batch 1
pilot protocol, without reading code or knowing the project's history.
**Date:** 2026-10-19. **State:** implemented and tested on CPU with synthetic
data; independently audited twice; the second audit's findings are
addressed. Nothing has been run on a model, nothing is formally approved, and
Freeze 1 has not been made.

## What to read, in order

| order | document | what it gives you | time |
|---|---|---|---|
| 1 | [`PROTOCOL_REVIEW.md`](PROTOCOL_REVIEW.md) | the study in plain language (§1), then all 14 decisions, each with the question, why it matters, the proposal, justification, alternatives, trade-offs, a recommendation, evidence and files | 40 min |
| 2 | [`TOPIC_REVIEW.md`](TOPIC_REVIEW.md) | **D05:** the 88 rewritten questions side by side with the originals and the historical questions they overlapped, and how they were checked | 25 min |
| 3 | [`COVERAGE_SIMULATION_REVIEW.md`](COVERAGE_SIMULATION_REVIEW.md) | **D11:** the simulation study of 15 coverage rules on 12 scenarios, and the recommended rule | 25 min |
| 4 | [`FINAL_APPROVAL_CHECKLIST.md`](FINAL_APPROVAL_CHECKLIST.md) | every approval and action needed before Freeze 1, with its status | 5 min |
| 5 | [`REMEDIATION_REPORT.md`](REMEDIATION_REPORT.md) | technical record: audit findings and fixes, files, tests, and how to reproduce | reference |

## The decisions in one table

| decision | recommendation | needs |
|---|---|---|
| D01–D04, D06–D08 | approve | your approval |
| D05 topic bank | approve after reading the 88 replacements | your review of `TOPIC_REVIEW.md` §3 |
| D09, D10 | approve with the disclosed noise | your approval |
| **D11 coverage** | **revise: P3 minimum 3** (P1, P2 stay at 2) | **your choice of rule** |
| D12 software and models | approve after the host smoke test; Python 3.11 already approved by you | host set-up, attestation, smoke test |
| D13 weights | approve with the disclosed concentration | your approval |
| D14 diagnostics | approve as diagnostics, not gates | your approval |

## What changed in this round, briefly

- **Topics (D05):** the 11 restatements the re-audit named were rewritten.
  A semantic review of the whole bank found 49 more, plus 5 duplicates and
  23 near cases; 88 questions were rewritten in all and checked twice more.
  The split is unchanged.
- **Coverage (D11):** admission keeps every qualifying reference (verified).
  12,000 simulated pilots show that false FEASIBLE verdicts come from ±0.10
  matching noise. A P3 minimum of 3 cuts them from 73% to 18% where coverage
  is thin, for about 1 point of extra false INFEASIBLE elsewhere. No minimum
  makes the reference populations cleaner.
- **Python (D12):** 3.11 is pinned, recorded in every approval and in Freeze
  1, and enforced with a clear message. Code fingerprints are now identical
  under Python 3.11, 3.12 and 3.13. The vLLM backend runs on Python 3.12, its
  pinned version, which needs your approval.
- **Safeguards:** Freeze 2 now binds backend provenance, so synthetic outputs
  cannot be passed off as real by editing metadata. Each retry keeps its own
  backend log; a row that always fails stops after 3 attempts; the smoke test
  avoids A and B; and a near-threshold flag is added.

## Is it ready?

**Ready for your final review. Not yet ready for Freeze 1.** Freeze 1 needs:

1. your approvals of D01–D14 in `approvals.json`, including your D11 choice;
2. the generation environment built, attested, and passing the smoke test.

See [`FINAL_APPROVAL_CHECKLIST.md`](FINAL_APPROVAL_CHECKLIST.md).

## Other documents in this folder

| document | content |
|---|---|
| [`README.md`](README.md) | the implementation report (technical) |
| [`decisions.md`](decisions.md), [`approvals_template.json`](approvals_template.json) | generated: the decision register with payload hashes, and the template you fill in |
| [`CALIBRATION_PRECISION_REVIEW.md`](CALIBRATION_PRECISION_REVIEW.md) | the first precision simulation (budget, D07, D14) |
| [`topic_screen_report.md`](topic_screen_report.md) | generated: every topic revision, reviewed pair and profile |
| [`library_review.md`](library_review.md), [`compatibility_review.md`](compatibility_review.md) | generated: the 51 references with wordings, and which can coexist with each B limit |
| [`estimate.md`](estimate.md) | generated: generation counts (30,976 at most) and historical throughput |
| [`freeze1_proposed.json`](freeze1_proposed.json) | generated: what Freeze 1 would contain today (not authorisable: no approvals, no attested environment) |
