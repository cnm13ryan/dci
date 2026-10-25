# Final approval checklist: everything needed before Freeze 1

**Update 2026-10-25:** your decisions of that day are applied (Python 3.12 for the orchestrator, replacing 3.11; P3 minimum 3; the D05 topic edits; the CUDA backend and one worker per GPU) and are written up for transcription in [`DECISIONS_2026-10-25.md`](DECISIONS_2026-10-25.md). Where this document says otherwise, that file and the code are current.

**Status on 2026-10-19:** not ready for Freeze 1. The implementation is
ready for your review, but no decision is formally approved, D11 needs your
choice, and the generation computer has not been set up or attested.

Part of the Batch 1 review package; start at
[`RESEARCHER_REVIEW.md`](RESEARCHER_REVIEW.md).

**Status key:** **DONE** = finished and verified. **YOUR DECISION** = you
need to decide or approve. **TO DO** = an action, after your decisions.
**APPROVED BY YOU** = you stated it in conversation, but it is not yet
recorded in `approvals.json`.

## A. Scientific decisions

Each must be recorded as APPROVED in `approvals.json`, against its current
payload hash, with your name and the date. Explanations:
[`PROTOCOL_REVIEW.md`](PROTOCOL_REVIEW.md). Hashes:
[`decisions.md`](decisions.md).

| | decision | status | what is needed from you |
|---|---|---|---|
| D01 | 29 proposed instruction variants | YOUR DECISION | approve, or swap `pro.word.the` first |
| D02 | wording frames and prompt | YOUR DECISION | approve |
| D03 | text counting rules | YOUR DECISION | approve |
| D04 | compliance, empty and failed answers, retry limit 3 | YOUR DECISION | approve |
| D05 | pilot size and topic bank (88 questions rewritten) | YOUR DECISION | read [`TOPIC_REVIEW.md`](TOPIC_REVIEW.md); approve, or name questions to change |
| D06 | Stage 2 rule, no partial completion | YOUR DECISION | approve |
| D07 | B selection (15 points, 3 models, limits ≤ 85%) | YOUR DECISION | approve |
| D08 | A selection (6 of 8, 3 models, no per-model A) | YOUR DECISION | approve |
| D09 | eligibility at 20% | YOUR DECISION | approve with the disclosure |
| D10 | matching at ±10 points | YOUR DECISION | approve with the disclosure |
| D11 | coverage minimums and target | **YOUR DECISION: choose the rule** | choose: P3 minimum 3 (recommended), 3 from ≥ 2 operations, or the design's 2 (see [`COVERAGE_SIMULATION_REVIEW.md`](COVERAGE_SIMULATION_REVIEW.md) §8); then approve |
| D12 | models, decoding, cap 512, seeds, backend, Python | **Python 3.12 for the orchestrator and backend: YOUR DECISION of 2026-10-25** (replacing 3.11), with the conditions in `DECISIONS_2026-10-25.md` | approve after B3 and B4, including Python 3.12 for the backend |
| D13 | object types and weights | YOUR DECISION | approve with the disclosure |
| D14 | stability diagnostics, near-threshold record | YOUR DECISION | approve; flag rule and the near-threshold record in `DECISIONS_2026-10-25.md` |

If you choose a P3 minimum of 3, one value changes in
`src/dci/batch1/config.py` (`p3_min_additional_other_operation`) and the
review artifacts are regenerated. Only D11's hash changes, so approve D11
after that change.

## B. Before Freeze 1

| | item | status | notes |
|---|---|---|---|
| B1 | independent re-audit findings R1–R4 addressed | **DONE** | [`REMEDIATION_REPORT.md`](REMEDIATION_REPORT.md) §R |
| B2 | Python 3.12 pinned (3.11 until 2026-10-25), recorded and enforced; hashes independent of Python version | **DONE** | `.python-version`; every command refuses another version; tested under 3.11, 3.12 and 3.13 |
| B3 | build the generation environment (CUDA vLLM for the chosen host) and attest it: `python -m dci.batch1 attest-environment --backend-python <path> --out environment_lock.json` | **TO DO** | no CUDA backend environment exists yet. The lock is refused unless the backend is Python 3.12 and has vLLM |
| B4 | smoke test on that host: `smoke-plan`, then `smoke --authorize <plan hash> --max-rows 72` | **TO DO** | at most 96 responses, never evidence, no A or B instruction. It measures load time, throughput, truncation at 512 tokens, and whether blank answers arrive as expected |
| B5 | record approvals: copy `approvals_template.json` to `approvals.json`, and set APPROVED, your name and the date for each decision | **TO DO (yours)** | the template records `orchestrator_python: "3.12"`; the code never writes APPROVED |
| B6 | Freeze 1: `python -m dci.batch1 freeze-protocol --root <run root> --approvals approvals.json --environment-lock environment_lock.json` | **TO DO** | after B3–B5; not done yet, as you asked |
| B7 | `python -m dci.batch1 validate-freeze --root <run root>` returns no problems and the manifest says authorisable | **TO DO** | |

## C. After Freeze 1 (for orientation; each needs its own go-ahead)

| | item | status |
|---|---|---|
| C1 | Stage 1 → score → Stage 2 selection → Stage 2 → score → finalise | not started; needs your explicit approval to launch |
| C2 | Freeze 2 and your review of it (with the D14 flags and the D11 disclosure) | not started |
| C3 | Batch 2 (combined instructions) | not started; out of scope for Batch 1 |

## D. Safeguards in place (no action needed)

| safeguard | how it is enforced |
|---|---|
| no combined prompt in the pilot | the prompt template has one instruction line; every row is compared with the frozen design before generation; Freeze 2 counts instruction lines in the prompt bytes |
| no real generation without approval | `execute` refuses unless Freeze 1 validates, every decision is APPROVED against its hash, the live environment matches the lock, and the Freeze 1 hash is passed |
| synthetic results cannot pass as real | real roots accept only rows with the backend's full output schema and runs recorded under the attested environment; Freeze 2 binds every backend-run record (new, R4.1) |
| logs survive retries | one directory per backend attempt (new, R4.3) |
| a row that always fails cannot loop | it is not retried after 3 technical failures, and the stage stays incomplete (new, R4.4) |
| the smoke test cannot reveal A or B results | it uses only non-focal instructions (new, R4.2) |
| the wrong Python cannot sign or run | every command refuses a Python other than 3.12, with the reason (new, R2) |
