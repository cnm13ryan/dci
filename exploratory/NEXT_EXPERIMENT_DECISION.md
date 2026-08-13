# Next-experiment decision

The measurement system is repaired. The question is what to run next, and the
evidence now points somewhere different from where the programme was heading.

## The finding that reorganises the priorities

Across every checkpoint measured, including the canonical one, the focal and
reference instructions are delivered at wildly different rates:

| checkpoint | condition | focal uptake (B) | reference uptake (C_L3) |
|---|---|---|---|
| Qwen3-4B (canonical) | natural, bracket | **0.075** | 0.900 |
| Qwen3-4B (canonical) | natural, semicolon | **0.100** | 0.925 |
| Qwen3-4B (canonical) | capped, all budgets | 0.000–0.150 | — |
| Qwen3.5-4B | NO_THINKING | 0.175–0.200 | 0.975–1.000 |
| Qwen3.5-9B | NO_THINKING | 0.275 | 1.000 |
| gemma-4-E4B-it | NATURAL | 0.525–0.550 | 1.000 |
| gemma-4-12B-it | NO_THINKING | 0.900–1.000 | 1.000 |

The two instructions are:

* **B (focal)** — *"Make each sentence strictly longer than the preceding
  sentence when measured by word count."* — **relational**: requires
  identifying units and comparing them pairwise.
* **C_L3 (reference)** — *"Begin every sentence with a word whose first letter
  is S."* — **local**: a per-unit surface check.

This is the surface-checkability distinction, and it is not a subtle effect: a
five- to twelve-fold gap in treatment delivery, consistent across four
checkpoints and two model families.

It matters for two reasons at once, and the second is the one that changes the
plan.

1. It is direct evidence for shortcut family 1, from data already collected.
2. **It breaks the matched-reference design.** The reference exists to control
   generic compositional load. If it is executed ~100% of the time while the
   focal is executed 10% of the time, the two slot occupants are not
   exchangeable, and τ conflates "focal instruction present" with "focal
   instruction far harder". Every DCI estimate in the programme rests on this
   pairing.

So the leading shortcut hypothesis and the leading identification defect are the
same fact. That is unusual and it is what makes the choice below dominate.

---

## Update: the bounded-thinking run set strengthens this

Since this document was written, the identification layer was wired into the
reporting pass and a fourth checkpoint (Kimi-VL) completed. The evidence for the
recommendation below is now stronger, not weaker.

| checkpoint | condition | focal uptake (B, relational) | reference uptake (C_L3, local) |
|---|---|---|---|
| Kimi-VL | bounded thinking, semicolon | **0.088** | 0.571 |
| Kimi-VL | bounded thinking, bracket | **0.405** | 0.531 |
| Qwen3.5-4B | bounded thinking | 0.967–1.000 | 0.975–1.000 |
| Qwen3.5-9B | bounded thinking | 0.972–1.000 | 1.000 |

Kimi-VL is the sharpest case yet: it is the **only** checkpoint whose target is
not saturated (target failure 0.559 focal against 0.286 reference, τ = +0.278
[0.056, 0.500]), and it is `FOCAL_NONUPTAKE` because the relational focal
instruction was satisfied in 8.8% of answered focal rows. The one checkpoint with
real headroom is the one where the treatment was least delivered.

The two Qwen checkpoints show the opposite pattern under bounded thinking —
near-total uptake in both arms — and they yield the programme's first two
IDENTIFIED cells, both small (+0.031 and +0.026, intervals touching zero). So
uptake is not a fixed property of the focal instruction: it moves with the
reasoning condition. That is itself a result Experiment 1 should absorb, and it
means the local/relational contrast must be measured under a declared reasoning
condition rather than pooled across conditions.

Nothing here changes the ranking. Experiment 1 remains the recommendation.

---

## Experiment 1 — Local-versus-relational, across multiple constraint families

**Hypothesis.** Constraints reducible to a local surface operation obtain
substantially higher behavioural compliance than constraints requiring
relational or global computation, independently of which punctuation mark or
which specific instruction is used.

**Competing explanations.** (a) B is simply harder in some family-neutral sense
(length, rarity, ambiguity) rather than relationally harder; (b) B is unusually
awkward to satisfy jointly with "exactly 4 sentences" specifically, so the gap
is a composition artifact rather than a property of B; (c) the verifier for B is
stricter than the verifier for C_L3, so the gap is measurement, not behaviour.

**Estimand.** Isolated compliance
U(c) = P(constraint satisfied | constraint presented alone, task population),
and the local-minus-relational contrast within each family,
Λ_f = U(local_f) − U(relational_f), reported per family, never pooled first.

**Manipulation.** Four constraint families, each with a matched local and
relational member, matched on word count, clause count and nominal difficulty:

| family | local member | relational member |
|---|---|---|
| lexical | begin every sentence with a word starting with S | make each sentence begin with a word alphabetically after the previous sentence's first word |
| counting | use exactly 4 commas in the whole answer | use one more comma in each sentence than in the previous sentence |
| length | keep every sentence under 12 words | make each sentence strictly longer than the preceding one |
| positional | put a number in the final sentence | put the answer's longest word in its shortest sentence |

**Control.** Each member is presented **alone** with the task, so composition is
not part of the measurement. Prompt length and instruction count are matched
within a family; family is a blocking factor, not a pooled unit.

**Identification gate.** Verifier certification for all eight constraints on an
adversarial fixture before any run — this experiment is *about* compliance
rates, so a differential verifier error would be fatal. Reject the family if
either member's verifier disagrees with human labels on a held-out sample.

**Minimum pilot.** 8 constraints × 20 tasks × 2 replicates = **320 generations**
on Qwen3-4B, the canonical checkpoint. At the observed batched throughput
(~4 s/row) this is roughly **25 minutes on one card**, no new backend work.

**Success/failure criterion.** Success: Λ_f > 0.3 in at least 3 of 4 families,
with paired-task intervals excluding zero. That would establish locality as a
property class rather than a property of one instruction. Failure: Λ_f varies in
sign across families, which would refute the general claim and reduce it to a
fact about B specifically — equally publishable and equally decisive.

---

## Experiment 2 — An admitted, uptake-matched reference family

**Hypothesis.** A reference matched to the focal on *realised uptake* rather
than on nominal slot occupancy yields an identified τ where the current
reference does not.

**Competing explanation.** τ is genuinely near zero for these configurations,
and the current reference is fine.

**Estimand.** τ^(j) per reference j, reported separately and never averaged, as
the framework requires. Range across j is the summary.

**Manipulation.** Replace the single reference with **three** independently
admitted references spanning the uptake range measured in Experiment 1: one
local (high uptake, the current C_L3), one relational (uptake matched to B), one
intermediate.

**Control.** The focal arm is unchanged, so τ^(j) differences are attributable
to the reference.

**Identification gate.** Every reference must clear: uptake ≥ 0.5, absolute
target damage < 0.5 (not `REFERENCE_CONTAMINATED`), and admission chosen from
calibration data **before** any focal result is seen.

**Minimum pilot.** Reference screening only: 3 references × 20 tasks × 2
replicates = **120 generations**, ~10 minutes. The full contrast is run only if
at least two references are admitted.

**Success/failure criterion.** Success: at least two admitted references, and
τ^(j) either stable across them (the effect is focal-specific) or strongly
reference-dependent (the effect is a difficulty contrast). Both outcomes are
informative; the current design cannot distinguish them at all.

---

## Experiment 3 — Trace re-priming versus plan-transcription failure

**Hypothesis.** One of two mechanisms explains why natural reasoning leaves
semicolon target damage intact: the trace re-primes semicolon-like structure, or
the trace plans four sentences correctly and the realisation violates the plan.

**Competing explanations.** The two are mutually exclusive in their predictions,
which is why this is worth running: re-priming predicts *more* semicolon-like
structure in the trace → *more* final-answer failure; plan-transcription
predicts a *correct explicit plan* co-occurring with failure.

**Estimand.** P(target failure | plan correct) versus P(target failure | plan
absent or incorrect), and the association between trace semicolon density and
final-answer failure, both within the focal semicolon arm.

**Manipulation.** None — this mines the **160 stored natural-reasoning traces**
that already exist. No new inference.

**Control.** The bracket arm's traces, same checkpoint, same condition.

**Identification gate.** The trace-labelling procedure must be frozen before
use and validated on a held-out human-labelled sample of 40 traces. If automated
labels disagree with human labels beyond a pre-declared margin, the analysis
stops and the labels are not used for inference.

**Minimum pilot.** **Zero generations.** Human labelling of 40 traces, perhaps
two hours. This is the cheapest informative thing available.

**Success/failure criterion.** Success: the two hypotheses separate — one
predictor is associated with failure and the other is not. Failure: neither
associates, which redirects attention to the answer-generation step rather than
the trace.

---

## Experiment 4 — Restoring target headroom on modern checkpoints

**Hypothesis.** gemma-4's `TARGET_CEILING` reflects an easy target rather than
an absence of interference; at a calibrated operating point, DCI-like behaviour
appears.

**Competing explanation.** Modern checkpoints genuinely compose these
instructions without interference.

**Estimand.** τ under a **calibrated** target difficulty. Reported as a
*calibrated operating-point* study and never pooled with fixed-contract
transport, because they answer different questions.

**Manipulation.** A small calibration grid over target difficulty (exact
sentence count 4 → 6 → 8) and load (k = 3 → 5), selecting the operating point
where baseline target failure lands in 0.2–0.6 on **held-out calibration tasks
only**.

**Control.** The fixed-contract cell is retained and reported beside it, so the
comparison between "instrument does not transport" and "behaviour appears when
recalibrated" is explicit.

**Identification gate.** The calibration rule is frozen before any DCI estimate.
Calibration tasks are disjoint from estimation tasks.

**Minimum pilot.** Calibration only: 6 operating points × 10 held-out tasks × 2
replicates = **120 generations** on gemma-4-E4B-it, ~10 minutes. DCI estimation
runs only if an operating point lands in the target band.

**Success/failure criterion.** Success: at least one operating point yields
baseline failure in 0.2–0.6, restoring headroom. Failure: no operating point
does, which is itself the finding — the instrument is ceiling-prone on this
model class and should be replaced rather than retuned.

---

## Ranking

| | discriminative | construct validity | restores identification | compute | complexity |
|---|---|---|---|---|---|
| 1. local vs relational | **high** | **high** | **high** — fixes the reference | 320 gens | low |
| 2. reference family | medium | high | **high** | 120 + 320 gens | medium |
| 3. trace analysis | **high** | medium (frozen labels needed) | none | **0 gens** | low |
| 4. headroom calibration | medium | high | medium (one family only) | 120 + 320 gens | medium |

---

## Recommendation

**Run Experiment 1 first, with Experiment 3 in parallel.**

Experiment 1 dominates because it is the only candidate that is simultaneously
the leading scientific question and the binding identification defect. Every
other DCI estimate in the programme depends on the matched-reference assumption,
and that assumption is currently false in a measured, five- to twelve-fold way.
Until the local/relational asymmetry is characterised, Experiments 2 and 4 would
produce more estimates resting on the same broken pairing — and a calibrated
operating point chosen while the reference is unmatched would bake the defect
into the calibration.

It is also the cheapest of the three that require generation: 320 rows, ~25
minutes, one card, no new backend, no vLLM work, and it runs on the canonical
checkpoint where the instrument is already validated.

Experiment 3 runs alongside because it costs **no generations at all** and its
main risk is analytic (label validity), which is handled by freezing the
procedure and validating on held-out human labels.

**Explicitly not recommended now:** any further cross-model grid. The cross-model
study is blocked by two separate identification failures, not by engineering.
Making Kimi or Gemma technically runnable under vLLM TP=2 would add checkpoints
to a design whose reference is unmatched and whose target is at ceiling — more
runnable models, zero additional identified cells. The framework's warning
applies directly: do not solve a failed scientific gate with an engineering
workaround.

## A recommendation about the instrument itself

If Experiment 1 confirms the locality effect at the predicted size, the honest
conclusion is that the **current instrument should change**, not be re-tuned.

"Exactly N sentences" as target, paired with a relational focal, has two
structural weaknesses now measured rather than suspected: it saturates at
ceiling on modern checkpoints, and its focal instruction is delivered so rarely
that the matched-reference design does not hold. A target and focal pair chosen
to be *matched in locality class* and *calibrated for headroom* would give a
benchmark that transports, where the present one demonstrably does not.
