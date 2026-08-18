# Pre-registered diagnostic experiment plan — Gate 1 model-judge stability

Committed BEFORE any experiment below is run. All thresholds, rejection
rules, sampling procedures, and measurement rules here are fixed in
advance; results must be interpreted against these criteria, never the
reverse. Everything is diagnostic: no registered DCI-1 v3 evidence is
modified, no judge configuration is approved, nothing here changes the
frozen verifier or the one-shot calibration record.

Scientific question: why do the judgments change, and can a measurement
process be designed in which the model judge is stable and agrees
closely with careful human judgment while requiring minimal human
annotation?

Baseline facts motivating the design (from the completed three matched
runs over the 370-sample diagnostic dataset):

* truncation at the 2048 cap: high 30, medium 4, low 2;
* label flips between the registered offline execution path and the
  Inspect/API path at FIXED effort, on the 61 previously-stable
  controls: low 9, medium 4, high 4 (plus 1–2 status changes each) —
  the "15/61 controls flipped" figure decomposes into these
  per-effort path effects;
* low vs medium label disagreement 193/370 within the API path.

## E1 — Output-cap search (run first)

Dataset `dataset/exp1_cap.jsonl`: every sample truncated in any of the
three completed runs (30 high ∪ 4 medium ∪ 2 low, deduplicated), plus
~30 matched near-miss controls: for each truncated sample the
non-truncated sample from the same (source model, target n) with the
largest high-effort completion tokens, topped up with the globally
longest non-truncated completions. Matched controls establish that
raising the cap does not change labels for samples the cap never
affected.

Server: same pinned stack/checkpoint/revision, `--max-model-len 12288`
(the only change; prompts are ≤ ~850 tokens so 8192-token completions
fit). Grid, all on this server, concurrency 4, fixed sorted order:

* effort ∈ {low, medium, high} × cap ∈ {4096, 8192}
* high × 2048 (paired control for the max-model-len server change)

Recorded per run and per sample: id, effort, cap, reasoning chars,
final-answer chars, completion tokens, stop reason (natural stop vs
cap), raw final answer, parsed label, status.

Decision rule (fixed): the safe cap C\*(effort) is the smallest cap in
{2048, 4096, 8192} such that (a) zero cap-stops among the E1 samples at
that cap and (b) every sample's (status, label) is identical at the
next larger cap. If any sample still cap-stops at 8192 at some effort,
run 16384 once for those samples only; if a sample cap-stops at 16384
it is classified "unbounded reasoning" — an operational failure mode of
that effort, reported, not chased further.

No scientific comparison between efforts is made at a cap where either
effort still cap-stops.

## E2 — Repeated-run stability (after E1 fixes C\*)

Dataset `dataset/exp2_repeat.jsonl`: all 61 controls + 59 contested
samples stratified by (source model, verifier class) sorted-id-first =
120 samples.

Design: for each effort ∈ {low, medium, high}, THREE identical
back-to-back runs at cap C\*(effort), same server, same order, same
seed, concurrency 4 (the diagnostic path's operating condition).
Nothing varies within a triple.

Metrics (fixed): within-setting instability = fraction of the 120
samples whose (parsed label, status) is not identical across the three
runs. Between-setting disagreement = fraction of samples whose
majority-across-runs labels differ between two efforts.

Acceptance threshold (fixed BEFORE results): a setting is
repeat-stable iff within-setting instability ≤ 2% (≤ 2/120 samples).
Context: the registered offline path's stability passes were 0/370
flips; 2% allows minor API-path nondeterminism, no more.

Attribution rule (fixed): a between-setting difference is treated as a
real reasoning-effort effect only where the between-setting
disagreement rate is ≥ 3× the larger of the two settings'
within-setting instability; otherwise it is not distinguishable from
run-to-run noise.

## E3 — Execution-path divergence (root cause, one factor at a time)

All comparisons are per-sample PAIRED on the 61 controls; every table
lists exactly which samples changed under which change.

* **3.0 Baseline pair** (already computed, no new runs): registered
  offline labels vs completed API-run labels at fixed effort
  (low 9 / medium 4 / high 4 label flips).
* **3.1 Parallelism/batching within the API path** (removed first, as
  required): Inspect runs on the 61 controls with `--max-connections 1`
  (fully serialized) vs `--max-connections 4`, same server, cap 2048,
  efforts low and high (the flip-affected settings). E2's repeat
  triples additionally measure concurrency-4 run-to-run noise.
* **3.2 Prompt rendering**: the registered offline path's
  `apply_chat_template(..., reasoning_effort=e)` token IDs vs the
  server's `/tokenize` of the identical conversation, per sample, CPU
  only. Identity ⇒ templating is excluded as a cause.
* **3.3 Engine and batch composition**: the registered offline engine
  (backend venv, same plan construction as the registered rounds,
  greedy, cap 2048, `skip_special_tokens=false`) run on the 61 controls
  at high effort with (i) chunk 32 — same chunk size as the registered
  rounds but a different batch composition (61 items rather than the
  full round), and (ii) chunk 1. If (i) differs from the registered
  labels, batch composition alone flips labels within the SAME engine.
  Also paired: high@2048 on the 4096-max-len server (completed run) vs
  high@2048 on the 12288-max-len server (E1 grid) isolates the
  server-settings factor.
* **3.4 Parsing**: for every paired disagreement, record whether the
  raw final answers are byte-identical (parser-caused) or different
  (generation-caused). Both parsers' vocabularies are already
  test-asserted equal; this check closes the loop per sample.

Root-cause standard (fixed): a factor is "the cause" only if toggling
it alone reproduces label changes of the same character while the
remaining factors are shown pairwise inert (token-identical prompts,
byte-identical outputs, or zero paired flips).

Consequence rule (fixed): the final Gate 1 calibration must use the
actual registered execution path (it already does) or an Inspect path
demonstrated equivalent under these paired tests. If equivalence fails,
the Inspect path remains diagnostic-only and every configuration-facing
conclusion from it must be re-checked on the registered path.

## E4 — Configuration rejection rules (fixed BEFORE results)

A reasoning-effort setting is REJECTED if any of:

1. **Cap-bound**: no cap ≤ 8192 achieves zero cap-stops on E1 samples,
   or truncation at C\* exceeds 2% when re-projected on the full
   370-sample diagnostic set.
2. **Repeat-unstable**: within-setting instability > 2% (E2).
3. **Path-dominated**: > 10% of the 61 controls flip label under ANY
   single E3 factor toggle at fixed effort (a judgment that depends
   this strongly on serving mechanics is not measuring the text).
4. **Mechanical errors**: among valid judgments on the mechanically
   unambiguous stratum |s0 − n| ≥ 2 (occurrence counts far from the
   target, checkable by exact counting), error rate vs the mechanical
   count > 10% at C\*.

Explicitly NOT a selection criterion: overall agreement with the
deterministic verifier (the verifier is the instrument under
validation).

## E5–E8 — Human review design (workflow built and tested now; real
labels only when a human annotator is available)

* **Diagnostic set** (~24, composition fixed): up to 6 medium-vs-high
  disagreements at C\*; 4 path-flip controls; 4 previously truncated;
  4 with response length ≥ P90; 3 with n ≥ 7; 3 where every surviving
  setting disagrees with the deterministic verifier; any
  Scout-validated flags. Never used to estimate overall accuracy.
* **Calibration set** (56 initial): stratified random sample from the
  FULL dev-half Gate 1 population (983 items), strata = source model ×
  verifier class, proportional allocation, simple random within
  stratum, seed 20260818, per-item inclusion probability recorded in
  the sample file. Extended only if the resulting uncertainty interval
  is too wide for a decision, by drawing additional items with the same
  procedure.
* **Blindness**: the reviewer interface shows ONLY the instruction, the
  frozen response, the SATISFIES/VIOLATES definitions, and fixed
  edge-case rules. Judge labels, verifier labels, effort, reasoning
  traces, and Scout flags are revealed only AFTER the human judgment is
  committed (append-only record with reveal timestamps).
* **No substitution**: model-generated labels are never recorded as
  human judgments. If no annotator is available the workflow stops
  after its dry-run self-test.

## E7 — Measurement rules (fixed BEFORE any final agreement is computed)

* Semantic outcomes: SATISFIES, VIOLATES. Operational states (never
  converted to a semantic outcome, never silently dropped):
  truncated/invalid_output, refusal, generation_failure, unscored.
* Sets: diagnostic = the 370-sample forensics dataset (+ E1/E2/E3
  reruns of its members); human-calibration = the 56-item stratified
  sample; reserved final check = 40 items (below). The sets are
  disjoint by construction from the held-out registered calibration
  items, which are never touched.
* A failed judge run counts against coverage, never as VIOLATES.
* Every report states: eligible examples, successfully judged examples,
  coverage = judged/eligible; agreement only over valid judgments.
* Aggregation: per-item pairing. Configurations are compared ONLY on
  identical human-labelled items, reporting the 2×2 discordant counts
  (config A right / config B wrong, and vice versa), per human-label
  class, plus each config's label base rates and coverage.

## E10 — Escalation triggers (pre-specified)

An item is escalated to a human when any of: output cap-stop;
unparseable final answer; any label flip across the 3 identical repeat
runs; surviving configurations disagree; a manually validated Scout
pattern fires; response length ≥ P95 of the population or n ≥ 7.
Reported: automation coverage (fraction not escalated) and, when human
labels exist, accuracy on the auto-handled subset.

## E11 — Reserved final check

40 items drawn by simple random sample (seed 20260818) from the 613
dev-half items NOT in the forensics dataset, disjoint from the human
calibration sample. IDs stored in
`experiments/reserved_final_check_ids.json` at build time; the file's
SHA-256 is recorded in the experiment log and the set is not run,
inspected, or used in any tuning until reasoning setting, cap, serving
setup, prompt, parsing, failure-handling, and escalation rules are all
frozen.

## E12 — Decision standard

`PROCEED` requires ALL of: cap no longer affects judgments;
within-setting instability ≤ 2%; calibration path = actual Gate 1 path
(or demonstrated equivalent); operational failures separated from
semantic errors; measurement rules frozen before scoring; human
calibration drawn from the real population; acceptable performance on
both human SATISFIES and human VIOLATES; no rejected configuration
meaningfully better on the same human labels; reserved final check
clean. Anything unresolved ⇒ `DO NOT PROCEED` with the missing
evidence enumerated. (Human annotation is currently unavailable, so
`DO NOT PROCEED` is the expected outcome of this phase; the deliverable
is the evidence that the remaining blockers are exactly and only the
human-label items.)
