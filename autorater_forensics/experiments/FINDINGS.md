# Consolidated findings — Gate 1 model-judge stability program

All experiments follow `PREREGISTERED.md` (committed before any run,
`e4c2303`). Everything here is diagnostic: no registered DCI-1 v3
evidence was modified, no judge configuration approved, nothing changed
in the frozen verifier or the one-shot calibration record. Judgments
are observations of a proxy instrument — never human validation,
ground truth, or semantic correctness.

## E1 — output cap

Cap-stops on the 70-sample E1 set (35 previously truncated + 35
matched near-miss controls):

| effort | 2048 | 4096 | 8192 | 16384 |
|---|---|---|---|---|
| low    | 2  | 0  | 0 | – |
| medium | 4  | 2  | 0 | – |
| high   | 30 / 20\* | 10 | 1 | 0 |

\* the same high@2048 condition produced 30 cap-stops on the
4096-max-len server and 20 on the 12288-max-len server: reasoning
LENGTH is itself run-nondeterministic. The single 8192 cap-stop
(`qwen3-4b-instruct-2507::…music-12…8:1`) stopped naturally at 3,486
tokens when rerun at 16384 — run-length variance, not unbounded
reasoning. No "unbounded reasoning" case exists.

Zero-cap-stop operating caps: **low 4096, medium 8192, high 8192.**

Label changes between consecutive-cap runs among non-cap-stopped
samples (3–7 per pair) match the concurrency-4 repeat-noise floor
measured in E2 and are therefore not attributable to the cap. Under
the strict pre-registered letter (labels identical at 2× cap),
C\* is "not established": that criterion turned out to measure
serving noise, not the cap. The cap-attributable effect is exactly
the cap-stop counts above.

## E2 — repeated-run stability (3 identical runs, conc=4, safe caps)

| setting | within-setting flips | verdict vs pre-reg 2% |
|---|---|---|
| low@4096    | 8/120 = 6.67% | FAIL |
| medium@8192 | 9/120 = 7.50% | FAIL |
| high@8192   | 7/120 = 5.83% | FAIL |

Between-setting (majority across runs, same subset):
low↔medium 35.0% and low↔high 35.0% — **real effects** (≥3× noise
floor); **medium↔high 13.3% — NOT distinguishable from noise**
(floor 22.5%) under concurrent serving.

## E3 — execution-path divergence (61 previously-stable controls)

| test | factor toggled | flips | byte-identical finals |
|---|---|---|---|
| T0 | prompt rendering (offline template vs server /tokenize) | 0/183 token mismatches | — |
| T1 | registered offline vs original API run | low 9, med 4, high 4 | low 37/60, high 14/59 |
| T2 | conc=1 vs conc=4, same server | low 3, high 2 | low 46/61, high 23/58 |
| T3 | API conc=1 vs registered offline | low 9, high 2 | low 32/61, high 11/60 |
| T4 | same engine, chunk 32, 61 items vs full-round composition | 5 | 12/60 |
| T5 | same engine, chunk 1 vs chunk 32 | 5 | 18/57 |
| T6 | offline chunk1 vs API conc1 (both single-stream) | 11 (4 are truncation-status diffs at cap 2048) | 10/56 |

Serialized repeatability probe: **3 identical conc=1 runs are
perfectly deterministic — low 0/61 flips with 61/61 byte-identical
final answers; high likewise 0/61 and 61/61.** The registered offline
path was already known to be exactly repeatable at fixed composition
(0/370 × 3 rounds).

**Root cause of the "15/61 control flips":** batch-composition-
dependent numeric nondeterminism. Prompt rendering is token-identical
(T0); parsing is inert (every paired disagreement differs in the raw
final text, none is parser-side; parser vocabularies are test-asserted
equal); concurrency contributes composition variance at runtime (T2,
and 0% instability at conc=1); and the registered engine itself flips
5/61 labels when only the co-batched items change (T4/T5). Between any
two execution contexts, ~80% of final answers differ at byte level;
each context is internally deterministic but produces its own labels
for boundary items. The engine-vs-server residual (T6) is of the same
magnitude and character as pure composition effects.

Flip anatomy: all 50 flip events across every E3 test concentrate on
18/61 items; 13 of those sit exactly one occurrence from the target
(|s0−n| = 1), while never-flipping controls are dominated by
|s0−n| = 0. Flip-prone responses are longer (mean 223 vs 158 words).
Low's path flips are direction-biased (8/9 fail→pass).

## E4 — narrowing (pre-registered rejection rules)

* **low: REJECTED.** Path-dominated (9/61 = 14.8% > 10% under the
  path toggle at fixed effort), repeat-unstable under concurrent
  serving (6.67%), direction-biased flips, and the weakest agreement
  with mechanical counts in the registered rounds (235 dev
  disagreements at 2048 vs medium 69 / high 28).
* **medium@8192 and high@8192: surviving candidates**, valid ONLY
  under a frozen deterministic serving context (registered offline
  fixed-composition seam, or serialized API). Under concurrent
  serving every setting fails the 2% repeat rule, and high exceeds
  the 10% path line on T6 (11/61 = 18%, of which 4 are cap-2048
  truncation-status diffs) — so no setting is acceptable unless the
  serving context is frozen into the instrument definition.
  Medium↔high cannot be separated without human labels (13.3% apparent
  disagreement is below the concurrent-serving noise floor; both are
  deterministic within a frozen context, where their differences on
  the 20 medium-vs-high disagreement items are real and stable —
  which of the two is RIGHT is exactly the human-calibration
  question).

## Why do the judgments change? (the scientific question)

1. **Truncation** at cap 2048 for high (30/20 of 70 hard items) —
   removed at cap 8192.
2. **Batch-composition numeric nondeterminism** under batched or
   concurrent serving — flips a stable, identifiable ~30% subset of
   boundary controls (|s0−n| ≈ 1, long responses); eliminated by
   freezing the execution context (serialize, or fix composition).
3. **Real reasoning-effort effects** — low genuinely differs from
   medium/high (35% ≫ noise); medium vs high at safe caps is small
   and not separable without human labels.

A stable measurement process therefore requires: one frozen serving
context declared part of the instrument; caps that never truncate
(8192); operational failures kept as statuses; pre-specified
escalation of boundary cases to humans; blind human calibration on a
population-representative sample; and an untouched final check.

## E10 — escalation (pre-specified triggers, computed)

On the 120-sample repeat subset with primary = high@8192:
60/120 escalated (triggers: difficult_range 45, configs_disagree 20,
repeat_flip 7). Population-projected via the contested/control mix
(309/674 of 983): **~45% escalated / ~55% automated**. The broad
`difficult_range` trigger dominates; it can only be narrowed after
human calibration shows where real errors live.

## Human-review stage (built, not yet run with humans)

Blind append-only review CLI (refuses piped input; reveal only after
commit), fixed SATISFIES/VIOLATES definitions and edge rules,
24-item diagnostic set (pre-registered composition), 56-item
stratified calibration sample with recorded inclusion probabilities
(seed 20260818), paired agreement report (per-class performance, base
rates, coverage, full tables, discordant pairs). End-to-end dry-run
verified; synthetic records refused by the report tool and deleted.
**No human labels exist; nothing here substitutes for them.**

## E11 — reserved final check

40 items, simple random from the 613 never-diagnosed dev-half items,
disjoint from the calibration sample, sealed in
`reserved_final_check_ids.json`
(sha256 `f8831598e275487037e6e51cd85e1df2b33c8e359d13836e500e9ab7b881d7a3`).
Not run, not inspected.

## E8 — human calibration results (added 2026-08-18 evening)

The researcher (single annotator, "Bryan" — also the study author;
real but not independent external validation) completed the 56-item
blind calibration review: all 56 items judged (0 UNSURE), ~52 minutes,
response hashes match the frozen pool, zero reveals before judgment,
zero synthetic rows.

**Human vs deterministic verifier: 56/56 = 100%** (exact 95% binomial
lower bound ≈ 93.6%). The frozen rule-based checker is human-anchored
on a population-representative sample: every human disagreement with
the study's instruments lies in the MODEL JUDGE, not the verifier.

Candidates on the same 56 human-labelled items (coverage in
parentheses; failures per the frozen rules count against coverage,
never as VIOLATES):

| configuration | context | correct among valid | human-SAT | human-VIO |
|---|---|---|---|---|
| high@8192   | serialized API (deterministic ×3) | **55/56 = 98.2%** (100%) | 39/39 | 16/17 |
| medium@8192 | serialized API | 51/56 = 91.1% (100%) | 37/39 | 14/17 |
| high@8192   | registered offline seam, chunk 32 | 50/54 = 92.6% (96.4%; 2 invalid) | 35/39 | 15/17 |
| medium@8192 | registered offline seam, chunk 32 | 52/56 = 92.9% (100%) | 37/39 | 15/17 |
| high@2048   | registered rounds (context) | 52/53 = 98.1% (94.6%) | 37/37 | 15/16 |
| medium@2048 | registered rounds (context) | 51/55 = 92.7% (98.2%) | 37/39 | 14/16 |
| low@2048    | registered rounds (context) | 40/56 = 71.4% (100%) | 29/39 | 11/17 |

Paired discordants on identical items: serialized-API context —
high right where medium wrong 4, medium right where high wrong **0**.
Offline context — 1 vs 1 (tie), 3 shared misses. **The candidate
ranking is context-dependent**: path equivalence between the two
deterministic contexts fails for high (51/56 identical judgments;
on all 3 label-level differences the API path matched the human) and
nearly holds for medium (55/56). The shared blind spot across every
configuration and context is one boundary miscount
(`…health-and-the-body-35…5:0`: 6 occurrences judged as 5; human and
verifier both say VIOLATES).

Rejected-configuration check: low (71.4%) is far below every surviving
candidate on the same labels — the rejection is confirmed by human
evidence, not just operational criteria.

## E12 — decision (superseded by the E8 addendum below)

**DO NOT PROCEED.** Missing evidence, exactly:

1. Human calibration labels (no annotator available) — blocking for:
   semantic validity of any configuration, medium-vs-high selection,
   per-class (SATISFIES/VIOLATES) performance, and narrowing the
   escalation triggers.
2. The final calibration execution path: the registered one-shot
   calibration DID use the actual registered path (satisfied), but any
   future human-anchored calibration must re-run judge labels in the
   frozen context under a truncation-free cap; the currently frozen
   registered config is high@2048, whose cap this evidence shows
   truncates ~8% of hard development items. Whether to amend the
   registered cap to 8192 (an audited supersession + new freeze cycle)
   is a researcher decision.
3. The reserved final check (must stay sealed until every rule is
   frozen).

Resolved by this program: output-limit effects (8192), repeat
stability (exact determinism in frozen contexts), root cause of path
divergence (batch-composition numerics; templating and parsing
excluded), failure-state separation, pre-registered measurement rules,
population-representative sampling design, blind review protocol.

## E12 addendum — after human calibration (2026-08-18 evening)

Against the §12 checklist: output-limit ✓ (8192; two residual offline
invalids noted), repeat stability ✓ (0% in frozen contexts),
failure separation ✓, rules frozen before scoring ✓, representative
human calibration ✓ (single-annotator caveat), both-class performance
✓ for high@8192-serialized (39/39 and 16/17), rejected configuration
confirmed worse ✓ (low 71.4%).

Still open — the verdict remains **DO NOT PROCEED**, now for exactly
three items:

1. **Configuration + context selection and freeze** (researcher
   decision): the evidence points to high@8192 in the serialized
   deterministic serving context (98.2%, 100% coverage, exact
   repeatability, dominant 4–0 in paired comparison); adopting it
   for Gate 1 requires an audited amendment of the registered
   autorater configuration (cap 2048 → 8192, serving context bound
   into the config) and a new freeze cycle. Keeping the current
   offline chunk-32 context instead leaves medium and high tied
   (~93%) with a known ~7% boundary-error band.
2. **Sealed reserved final check** (40 items,
   sha256 `f8831598e275…`): run once, only after (1) is frozen.
3. **Annotation independence**: the calibration labels come from one
   annotator who is also the study author. Blindness was enforced
   mechanically, but independent replication (a second blind
   annotator on the same 56 items, or an external reviewer) is the
   remaining validity upgrade.

Positive human-anchored results that need no further work: the
deterministic verifier is 56/56 with blind human judgment on the Gate 1
population; every model-judge configuration is measurably worse than
the deterministic verifier it was meant to validate.
