# Gate 1 development review, round 3 (amendment A3.2) — the reasoning-budget operating-point comparison

Third real `gate1-dev` round, 2026-08-17, producing commit `fe67cbc`,
under **autorater-config/4** (hash `dc8e5b8…`): reasoning_effort=**high**,
cap **2048** — both inside the hashed configuration — with everything
else held fixed (openai/gpt-oss-20b @ `6cee5e81…`, prompt
gate1-judge/2.0.0, parser gate1-parse/2.0.0, greedy,
`skip_special_tokens=false`, TP=1 two-GPU allocation, production sorted
order, chunk 32, verifier and split untouched). Rounds 1 (low/512,
`881d789…`) and 2 (medium/1024, `1b1b4df…`) are parked intact under
each model's `gate1/autorater/superseded/<config-prefix>/` — never
deleted. **No sign-off, freeze, or calibration has been run.**
Complete residual cases: `reports/gate1_dev_cases_r3.json`.

## Scratch cap selection (diagnostic set, never registered evidence)

At high effort the 1024 cap truncated 6/24 graded transcripts
(p90 = cap) — confounded. Cap 2048 is the smallest that unconfounds:
24/26 complete (gen tokens median 547, p90 1430); the two residuals ran
the full 2048 without concluding (deliberation loops, not budget), and
larger caps would crowd the judge's 4096-token context against the
longest pool prompts. Diagnostics: high/2048 22/24 vs medium/1024 23/24
— the field data below was therefore decisive.

## Execution (all four COMPLETED; no OOMs, crashes, retries; each phase on one TP=1 GPU)

| Model | GPU | Wall | Gen tokens (dev pass) med / p90 / mean | vs medium mean |
|---|---|---|---|---|
| gemma-3n-e2b-it | 0 | 30 m 49 s | 783 / 1874 / 891 | ×2.35 |
| qwen3-4b | 1 | 31 m 44 s | 424 / 1021 / 561 | ×1.93 |
| qwen3-4b-instruct-2507 | 0 | 27 m 37 s | 483 / 978 / 615 | ×1.89 |
| gemma-3n-e4b-it | 1 | 31 m 15 s | 755 / 1589 / 824 | ×2.53 |

Four-model phase: **63 m 01 s** wall (vs 29 m 41 s at medium) —
~2.2× tokens, throughput consistent with the serving benchmark.
Stability: **0 label flips, 0 status changes** in all four repeated
passes (983 repeated judgments), as in both prior rounds.

## Medium → high, per model

| Model | Disagreements | Rate (of valid) | Invalid (all finish=length) | Identification interval |
|---|---|---|---|---|
| gemma-3n-e2b-it | 19 → **8** | 0.081 → 0.035 | 11 → **20** | [0.878, 0.923] → [0.886, 0.968] |
| qwen3-4b | 8 → **1** | 0.033 → 0.004 | 1 → **7** | [0.963, 0.968] → [0.968, 0.996] |
| qwen3-4b-instruct-2507 | 30 → **12** | 0.124 → 0.050 | 4 → **6** | [0.861, 0.878] → [0.927, 0.951] |
| gemma-3n-e4b-it | 12 → **7** | 0.050 → 0.030 | 7 → **9** | [0.923, 0.951] → [0.935, 0.972] |
| **Overall (N=983)** | **69 → 28** | | **23 → 42** | **[0.906, 0.930] → [0.929, 0.972]** |

Per-item transitions (primary dev pass, all four models):
`wrong→correct` **48**, `correct→wrong` **11**, `correct→invalid`
**34**, `wrong→invalid` 4, `invalid→correct` **19**,
`invalid→invalid` 4, unchanged-correct 846, unchanged-wrong 17.

Round-3 2×2 tables (P/S, P/V, F/S, F/V): E2B 143/2/6/75;
qwen3-4b 172/1/0/66; instruct 155/3/9/72; E4B 189/1/6/41.
Residual disagreements by n concentrate at n ≥ 5 (by-n and by-source
detail in the cases file); direction is now predominantly
fail→SATISFIES (21 of 28) — under-counting on near-miss fail items —
with the over-count mode nearly eliminated.

## The six determinations

1. **±1 errors:** substantially reduced — 69 → 28 disagreements; net
   37 labeled errors corrected (48 fixed vs 11 introduced).
2. **High-n cases:** clearly improved — e.g. n=8 residuals 6→2 (E2B),
   6→2 (instruct); the saturation/severe-miscount mode is gone except
   one case.
3. **Truncation:** worse — invalids 23 → 42 despite the doubled cap
   (dense fail-class texts push even 2048); every one is a distinct
   `invalid_output`, `finish_reason=length`, never a label. Notably 19
   of medium's 23 invalids became *correct* under high, and none became
   wrong.
4. **New failure modes:** none qualitative. Same miscount family; one
   over-count-by-2 case (qwen `prescreen:music-12`); 11 correct→wrong
   regressions; no refusals, format breaks, or instability.
5. **Verifier defects:** none — all 28 residual disagreements are
   mechanically verified (S0 = independent reimplementation =
   word-boundary regex, 28/28); every case classifies as an autorater
   miscount.
6. **Cost vs benefit:** ~2.2× tokens and wall (63 vs 30 min for the dev
   phase; the remaining one-shot calibration would cost ~30 min at high
   vs ~15 at medium — immaterial in absolute terms for this study). The
   benefit is not merely "agreement went up": the **conservative lower
   bound of the full-set identification interval — which already prices
   in the extra invalids — improves for every model**, and overall the
   high interval [0.929, 0.972] sits entirely at or above medium's
   [0.906, 0.930].

## Recommendation: freeze the high-effort operating point

Freeze **autorater-config/4 (reasoning_effort=high, cap 2048, hash
`dc8e5b8…`)** as the calibration condition. Justification: strictly
better conservative agreement bounds on all four replications, halved
labeling error with no new failure modes, identical perfect stability,
and an absolute compute cost that is trivial at this study's scale. The
known trade-off — reduced coverage (95.7% vs 97.7%) from truncation on
dense texts — is transparent in the registered statuses and interval
reporting, and is the honest failure mode (abstention) rather than the
harmful one (mislabeling). Low effort is dominated; medium remains the
fallback if the researcher weighs coverage above labeling accuracy —
restorable exactly by re-registering the identical medium configuration
and re-running `gate1-dev` (greedy reproducibility under fixed
composition is established across three rounds).

## Pending researcher decisions (nothing below has been run)

1. Accept round 3 as the development basis and the high/2048 freeze
   operating point (or direct the medium restore).
2. Then: `gate1-signoff --phase development --notes …` →
   `verifier-freeze` → `gate1-calibrate` ×4 (one-shot) →
   `gate1-signoff --phase calibration` →
   `gate1 --model … --approve-autorater-calibration` ×4.
