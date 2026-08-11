<!-- Mirrored from runs/arbitration_program_20260811T185546Z/FINAL_RESEARCH_REPORT.md.
     exploratory/runs/ is gitignored, so the report is kept here where it is
     version controlled; the raw generations, figures, per-experiment reports,
     research log and audit stay in the run directory. -->

# Does more reasoning solve instruction conflicts, or change which instruction loses?

**6,282 generations across four sequential experiments**, all on the same 20
tasks, the same five instruction wordings, and the same verifiers.
`EXPLORATORY_NO_EVIDENCE` — nothing here is a protocol result.

| experiment | generations | question |
|---|---|---|
| seed smoke test | 128 | are replicate seeds distinct? |
| 1 · seed-corrected replication | 1280 | does the phenomenon survive correct seeds? |
| 2 · complete order map | 2560 | does a simple positional rule explain it? |
| 3 · priority intervention (+ bridge) | 960 + 32 | can an explicit priority change which instruction survives? |
| 4 · second model | 1280 + 42 | does any of it transport? |

---

## Research question

Three instructions are given at once: a **target** A ("Write exactly 4
sentences"), a **focal** instruction B ("Make each sentence strictly longer than
the preceding sentence") or its matched **reference** R ("Begin every sentence
with a word whose first letter is S"), and a **background** C — either "exactly
one semicolon, placed wherever you judge best" or the same sentence with "one
pair of round brackets".

All three are jointly satisfiable; Round 10 certified that with hand-authored
witnesses scored by these same verifiers. So every failure below is a model
failure on an achievable task.

Two explanations predict different things when reasoning is added.

* **Joint improvement.** More reasoning makes the model better at the whole task,
  so P(both instructions satisfied) should rise.
* **Arbitration change.** More reasoning changes *which* instruction is preserved
  when the model fails, so probability should move between "target only" and
  "focal only" without joint success improving.

The programme measures both from the same scored rows, so a result cannot be one
thing in one table and the other in another.

The two contrasts:

* **τ = P(A fails | B) − P(A fails | R)**, paired within task — interference
  attributable to the focal instruction rather than to carrying a third
  instruction at all.
* **Δ = τ(semicolon) − τ(brackets)**, paired — the extra interference caused by
  the semicolon background. **Positive Δ means the semicolon made the target fail
  more often.**
* **Γ = Δ(b=4096) − Δ(b=0)** — how much reasoning changes the semicolon's effect.

Intervals are 95% percentile cluster bootstraps over the 20 tasks, 10,000 draws,
resampling tasks with all their conditions and replicates attached. Exploratory,
uncorrected.

---

## Seed-corrected replication

### The seeding problem was real, and the in-tree repair was not enough

The original defect made ~98% of nominal replicate pairs byte-identical. The
repair already in the tree seeds from the **row's index in the design file**,
which fixes that but is still not a scientific seed: matched focal and reference
rows of one (task, replicate) draw different decoder noise, so the paired τ is not
a common-random-number difference, and reordering the design reseeds every unit.

This programme seeds from the experimental unit —
`blake2b(MASTER_SEED | task_id | replicate | phase)`. Validation: every replicate
of every task carries its own seed, thinking and answer phases are seeded apart,
and **0 of 192 replicate pairs are identical** with 4 distinct answers in all 32
smoke cells. Across the four main datasets the seed structure holds exactly:
one answer seed per (task, replicate), four distinct seeds per task, 0 rows
reusing the thinking seed.

### What replicated

| finding | Round 9/10 (buggy seeds) | here (correct seeds, 4 replicates) |
|---|---|---|
| reasoning abolishes ordinary interference | τ_control → 0 | **τ_control +0.412 → +0.037** (QAC), **+0.637 → +0.075** (ACQ) |
| semicolon interference survives reasoning | τ_amp stays high | **+0.688 → +0.550** (QAC) |
| joint success stays low | P(both) ≤ 0.15 | **P(both) ≤ 0.113** in Experiment 1; ≤ 0.225 in one of 24 cells overall |
| reasoning increases "target only" | yes | yes — "neither" 0.412 → 0.025 under the control at QAC |
| order changes the effect | yes | **yes, it reverses the sign**: Δ(b=0) = +0.275 at QAC, **−0.537** at ACQ |
| ACQ is especially reasoning-sensitive | yes | **yes: Γ_ACQ = +0.725** [+0.537, +0.925] vs Γ_QAC = +0.237 |

Every headline survived, and three are sharper than before — the ACQ reversal now
has an interval well clear of zero where the earlier estimate rested on one
effective draw per cell.

### What the corrected seeds changed

Nothing qualitative. The four replicates now agree: per-replicate Δ in
Experiment 1 has the same sign in all four replicates of all four cells, with a
spread of 0.15–0.35. That agreement is exactly what the old seeding could not
show, and it is the reason the effect sizes here can be quoted at all.

---

## Order experiment

Δ for all six permutations, at both budgets:

| order | Δ at b=0 | Δ at b=4096 | Γ |
|---|---|---|---|
| QAC | +0.275 [+0.013, +0.525] | +0.512 [+0.400, +0.625] | +0.237 [+0.013, +0.475] |
| QCA | +0.175 [−0.062, +0.400] | +0.550 [+0.425, +0.675] | +0.375 [+0.125, +0.637] |
| AQC | +0.000 [−0.237, +0.237] | +0.287 [+0.163, +0.412] | +0.287 [+0.050, +0.525] |
| ACQ | **−0.537** [−0.700, −0.362] | +0.188 [+0.013, +0.375] | **+0.725** [+0.537, +0.925] |
| CQA | +0.388 [+0.175, +0.613] | +0.375 [+0.237, +0.512] | −0.013 [−0.275, +0.237] |
| CAQ | +0.013 [−0.150, +0.163] | +0.062 [−0.113, +0.225] | +0.050 [−0.163, +0.287] |

**Stable across the map:** at b = 4096, Δ is positive in all six orders, with five
of six intervals excluding zero. Reasoning abolishes ordinary interference in all
six (τ_control at b = 4096 is −0.025 to +0.087, against +0.100 to +0.637 at
b = 0).

**Not stable:** at b = 0, Δ spans −0.537 to +0.388 — a range wider than any single
order's effect.

### The simplest explanation supported: none

Fourteen positional partitions were compared, each judged by whether its
between-group gap exceeds the larger within-group spread. Three separate a single
quantity, and only just:

| rule | quantity | gap | within-group spread | ratio |
|---|---|---|---|---|
| Q last (vs not) | Δ at b=4096 | −0.306 | 0.263 | 1.16× |
| Q before A | Δ at b=4096 | +0.300 | 0.225 | 1.33× |
| C in the middle | Γ | +0.409 | 0.350 | 1.17× |

The first two are one idea: the semicolon amplifies most when the focal
instruction precedes the target, least when it comes last. **No rule separates all
three quantities**, the ratios are near 1, and they were picked from fourteen
inspected. No model was fitted to six points.

**ACQ is singular and its singularity is not positional.** AQC shares "A first"
(Δ = +0.000), CAQ shares "Q last" (+0.013), QCA shares "C in the middle"
(+0.175). Only the conjunction picks out ACQ, and a conjunction selecting 1 of 6
cells describes rather than explains.

Diagnostic order, chosen by the pre-registered rule and recorded before any
cross-model data existed: **ACQ** (largest |Γ|, no tie-break needed).

---

## Priority intervention

Ψ = S(A over B) − S(B over A), where S = P(target only) − P(focal only). Direct
arbitration predicts Ψ > 0.

| background | b | Ψ |
|---|---|---|
| parentheses | 0 | +0.037 [−0.125, +0.200] |
| parentheses | 4096 | −0.013 [−0.113, +0.075] |
| semicolon | 0 | −0.087 [−0.212, +0.025] |
| semicolon | 4096 | −0.113 [−0.250, +0.025] |

**Reversing the stated priority did not reverse which instruction survived.** All
four intervals contain zero and three point estimates carry the wrong sign. The
one directional effect that clears zero runs against the prediction: at the
semicolon with b = 4096, `B > A` minus equal is **+0.163** [+0.013, +0.312] —
telling the model to prefer the focal instruction made the **target** more likely
to be the survivor.

It is not general assistance either: `both(A>B) − both(equal)` is **−0.062**
[−0.125, −0.013] at the semicolon with b = 4096, a trace of cue-induced damage.

**The cue was read.** Reasoning traces mention priority, preference or a trade-off
in 0.54–0.69 of directed rows against 0.21–0.39 under equal priority. So the null
is not inattention. The model attends to a stated priority and cannot act on it.

The **follow-up under ACQ was not run**, because the directive gates it on a clear
directional effect and there is none. `followup/` is empty and the reason is
recorded there.

---

## Cross-model replication

`HuggingFaceTB/SmolLM3-3B` — a distinct lineage, selected against all eight
eligibility requirements with four other candidates rejected in writing
(`cross_model/eligibility.md`), run on the byte-identical Experiment 1 design
(640 shared cells, 0 prompt mismatches).

| | Qwen3-4B | SmolLM3-3B | transports? |
|---|---|---|---|
| reasoning abolishes ordinary interference | +0.412 → +0.037 | +0.263 → +0.025 | **yes** |
| Γ positive, interval excludes zero | both orders | both orders | **yes** |
| P(both) stays low | ≤ 0.113 | ≤ 0.138 | **yes** |
| Δ at b = 0 | +0.275 (QAC) | **−0.463** (QAC) | **no — opposite sign** |
| Δ at b = 4096 | +0.512 | −0.062 | **no — amplification absent** |
| order interaction | Γ 0.237 vs 0.725 | Γ 0.400 vs 0.300 | **no** |

**The reasoning effect transports; the semicolon amplification and the order
interaction do not.** On SmolLM3 the semicolon is protective wherever it does
anything, and reasoning erodes that protection — the same *direction of change* as
Qwen3-4B's ACQ cell, from a different starting point.

Two limits weaken this comparison and cannot be re-analysed away: SmolLM3's
background compliance is **0.194–0.575** (against 0.706–0.938), so the
manipulation often did not land; and its reference arm's A-failure reaches
**0.675**, so τ is not a clean read-out of focal damage there. Conditioning on
compliance is post-treatment, was run only descriptively, and leaves Δ near zero
either way.

---

## Sanity checks

**Independent recomputation.** Every headline number was computed twice: once by
the analysis pipeline, once by `arb_verify.py`, which imports no estimand
function, no grouping helper and no bootstrap from the pipeline and rebuilds
τ, Δ, Γ, the four outcome probabilities, S and Ψ from the JSONL with the standard
library. **282 quantities compared across the four datasets; no disagreements.**
The same script re-derives `A_pass`, `Q_pass` and `background_pass` from the
answer text through the verifier rules: **0 mismatches across 7,360 row-checks over 6,080 distinct scored rows** (Experiment 1's rows are checked in both the Experiment 1 and the six-order dataset), so
the stored verdicts still mean what they say.

**Manual verification.** 57 Experiment 1 outputs were read: 20 across all
conditions, 10 target-only, all 7 focal-only, 10 both, 10 from the cell with the
largest A-failure swing. The registry's sentence count and an **independent
character-scanning segmenter** — different algorithm class, no shared helpers, no
shared abbreviation table — agreed **57/57**. Every hand-checked verdict matched
its programmatic label. Ids and texts in `independent_checks/exp1_inspection.txt`.

**The full check list** (`independent_checks/sanity_checks.txt`):

| check | result |
|---|---|
| request seeds | 1 answer seed per (task, replicate), 4 per task, 0 phase reuse, in all four datasets |
| arm construction | asserted at design time; 8 cells × 80 rows in Experiment 1 |
| identical wording across permutations | asserted: all six orders share component sets and differ only in line order, in all 320 matched groups |
| background / reasoning condition | `native_nonthinking` = 1.000 at b = 0, 0.000 at b = 4096, in every dataset |
| fixed final-answer budget | 512 in every row of every dataset |
| verifier correctness | independent segmenter agreement 57/57; 0 re-derivation mismatches |
| truncation | 0.0008–0.0047 by dataset |
| technical failure | **0.0000 everywhere** |
| reasoning leakage | 0.0008–0.0047 |
| task concentration | 12–19 of 20 tasks contribute non-zero to Δ; top-3 share 0.24–0.67 |
| seed concentration | per-replicate Δ agrees in sign in every Experiment 1 cell, spread 0.15–0.35 |
| background compliance | Qwen3-4B 0.537–0.988; **SmolLM3-3B 0.125–0.713 — flagged** |
| priority-cue compliance | traces mention the cue in 0.54–0.69 of directed rows vs 0.21–0.39 |
| response-length changes | sentence count 2.9–4.4, word count 74–165; the semicolon consistently *shortens* the answer, by 0.35-0.72 sentences on Qwen3-4B and 0.42-1.17 on SmolLM3-3B |
| floor / ceiling | **B is on the floor (0.000–0.138)**; the reference arm's A_pass is at ceiling in 5 cells |
| baseline movement | Qwen3-4B reference arm 0.000–0.087 (clean); **SmolLM3 0.087–0.675 — flagged** |

Two flags are load-bearing and appear in the limitations rather than being
absorbed: the focal instruction's floor, and SmolLM3's background compliance.

---

## Observations

Only what was measured.

1. Reasoning reduces τ under the bracket control from +0.100…+0.637 to
   −0.025…+0.087, in all six orders.
2. Reasoning does not reduce τ under the semicolon: +0.550 at QAC with b = 4096.
3. Δ at b = 4096 is positive in all six orders (five intervals exclude zero).
4. Δ at b = 0 ranges from −0.537 (ACQ) to +0.388 (CQA).
5. P(both) is ≤ 0.113 in Experiment 1's eight cells and reaches 0.225 in exactly
   one of the 24 cells of the order map.
6. Reasoning moves probability from "neither" to "target only" under the control
   in all six orders; under the semicolon it moves it the *other* way in five.
7. The focal instruction B is satisfied in 0.000–0.138 of focal-arm generations
   under every condition tested; the reference C_L3 rises from 0.237–0.475 to
   0.912–0.963 with reasoning.
8. Ψ is null in all four cells; `B>A − equal` is +0.163 [+0.013, +0.312] at the
   semicolon with b = 4096.
9. Priority cues appear in 0.54–0.69 of directed reasoning traces.
10. On SmolLM3-3B, Γ > 0 in both orders, Δ < 0 at b = 0 in both, Δ ≈ 0 at
    b = 4096 in both.
11. The semicolon background reduces mean sentence count by ~0.5 relative to the
    bracket control at matched budget, on both models.
12. The semicolon constraint is sometimes satisfied degenerately — `…itself.; The`
    or a free-standing `;` between sentences — which the verifier accepts, and
    which shows the mark can be discharged without joining clauses.

---

## Supported interpretation

**Within the tested conditions:**

* **More reasoning does not buy joint satisfaction.** Across 24 order × background
  × budget cells, joint success stays below 0.15 in 23 of them. What reasoning
  reliably buys is the *target*.
* **What reasoning does is remove one kind of interference, not all of it.**
  Ordinary focal-versus-reference interference is abolished by 4096 tokens of
  reasoning in every order and on both models. Semicolon-conditioned interference
  is not touched on Qwen3-4B.
* **The direction of the background's effect is not a property of the background.**
  The same sentence, moved to a different slot, changes Δ from −0.537 to +0.388.
  Any account of "what a semicolon does to instruction-following" that does not
  mention position is wrong.
* **Reasoning is not an instruction-ranking mechanism.** Reasoning changes which
  instruction survives; an explicit instruction to rank does not. This is the
  cleanest result in the programme, and it is negative.

**Between models:** the *reasoning effect* is not specific to Qwen3-4B; the
*amplification* and the *order interaction* have not been shown outside it.

---

## Remaining hypotheses

* **The semicolon acts through the sentence boundary.** It shortens answers by
  ~0.5 sentences on both models and is sometimes satisfied by a mark standing
  where a boundary would go. Untested: whether a mark that is equally unattached
  and freely placeable but *cannot* occupy a clause boundary behaves differently.
* **The order effect is about what the model has already committed to when it
  reads C.** Suggested by "Q before A" separating Δ at b = 4096, contradicted by
  nothing, established by nothing.
* **B may be unreachable rather than deprioritised.** Its 0.000–0.138 compliance is
  consistent with a capability limit on cross-sentence length comparison, which
  would explain the priority null without any arbitration mechanism.

---

## Failed explanations

* **Explicit priority ranking. Falsified within these conditions.** Ψ null in four
  cells, with the one significant contrast pointing the wrong way, while the cue
  is demonstrably read.
* **Joint improvement as the account of what reasoning does. Falsified.** P(both)
  ≤ 0.225 in every cell of every experiment, and reasoning raises it by at most
  0.11 while moving 0.2–0.6 of probability mass between other outcomes.
* **A simple positional rule for the order effect. Not supported.** Fourteen
  partitions, none separating more than one quantity, none by more than 1.33× its
  own within-group spread.
* **A moving reference baseline as the source of τ on Qwen3-4B. Ruled out.**
  Reference-arm A-failure is 0.000–0.087 in all eight Experiment 1 cells. (On
  SmolLM3 it is *not* ruled out and is reported as a limit.)
* **The earlier effect sizes. Superseded, not reproduced.** The programme treats
  them as unreliable by construction and none was used as a target.

---

## Limitations

* **Task sample.** 20 tasks from one pilot split. Every interval is a bootstrap
  over these 20 and describes no wider population.
* **Stochastic uncertainty.** 4 replicates per cell. Per-replicate Δ spreads of
  0.15–0.40 mean differences smaller than ~0.2 are not resolvable at the cell
  level, even where the task-clustered interval is narrower.
* **Model specificity.** Two models. The amplification result rests on one.
* **Prompt specificity.** One paraphrase (index 0) of each instruction, one task
  phrasing, no system message on Qwen3-4B and the model's own on SmolLM3.
* **The focal instruction is on the floor.** B is satisfied 0.000–0.138 of the
  time. "Focal only" occurs in 7 of 640 Experiment 1 rows, so the arbitration
  measured is overwhelmingly *target versus nothing*, not *target versus focal*.
  This is the single largest limitation on reading these results as arbitration.
* **The reasoning intervention is a budget, not a dose of thought.** b = 4096 is
  near-unconstrained (cap-hit 0.011–0.056) and b = 0 is a native template mode;
  realised reasoning is post-treatment and is never conditioned on.
* **Leakage and truncation.** Small but non-zero (≤ 0.005). Not gated to zero.
* **Exploratory multiplicity.** Roughly 280 intervals are reported. None is
  corrected for multiple comparisons, and fourteen positional rules were inspected
  before three were quoted. Individual borderline intervals should be read as
  descriptive.
* **Cross-model comparability.** SmolLM3's background compliance (0.194–0.575) and
  moving reference baseline (to 0.675) mean its nulls are weaker evidence than
  Qwen3-4B's positives.

---

## Next experiment

**One:** test whether the semicolon's effect runs through the sentence boundary,
by contrasting it against a mark that is equally unattached and equally free to
place but **cannot** stand at a clause boundary — an asterisk or a degree sign —
at matched compliance, at QAC and ACQ, at b = 0 and b = 4096.

Why this one. The programme has now falsified the priority-ranking account,
falsified joint improvement, and failed to find a positional rule; what survives
is that the amplifying mark is unattached, freely placed, and *could* occupy a
sentence boundary. Every result here is consistent with that and none tests it.
The two degenerate satisfactions found by hand (`…itself.; The` and a
free-standing `;`) plus the shortening the semicolon causes on **both** models
(0.35-0.72 sentences on Qwen3-4B, 0.42-1.17 on SmolLM3-3B) are the first positive evidence pointing at it, and both are
incidental observations rather than manipulations.

It is also the cheapest decisive test available: ~1280 generations, one new
constraint id in the registry, no new model, no new engine. A boundary-capable
mark that amplifies and a boundary-incapable mark that does not, at matched
compliance, would be the first *positive* intervention on the mechanism rather
than another elimination.

---

## Run directory

```
runs/arbitration_program_20260811T185546Z/
```

  AUDIT.md
  cross_model/eligibility.md
  cross_model/main/design.jsonl
  cross_model/main/manipulation_check.txt
  cross_model/main/raw_generations.jsonl
  cross_model/main/report.txt
  cross_model/main/scored_generations.jsonl
  cross_model/main/scoring.txt
  cross_model/report.md
  cross_model/smoke/DECISION.md
  cross_model/smoke/design.jsonl
  cross_model/smoke/raw_generations.jsonl
  cross_model/smoke/report.txt
  cross_model/summary.csv
  environment.json
  figures/data/fig1_core_replication.csv
  figures/data/fig2_arbitration_outcomes.csv
  figures/data/fig3_six_orders.csv
  figures/data/fig4_priority_intervention.csv
  figures/data/fig5_cross_model.csv
  figures/fig1_core_replication.pdf
  figures/fig1_core_replication.png
  figures/fig1_core_replication.svg
  figures/fig2_arbitration_outcomes.pdf
  figures/fig2_arbitration_outcomes.png
  figures/fig2_arbitration_outcomes.svg
  figures/fig3_six_orders.pdf
  figures/fig3_six_orders.png
  figures/fig3_six_orders.svg
  figures/fig4_priority_intervention.pdf
  figures/fig4_priority_intervention.png
  figures/fig4_priority_intervention.svg
  figures/fig5_cross_model.pdf
  figures/fig5_cross_model.png
  figures/fig5_cross_model.svg
  figures/FIGURE_CAPTIONS.md
  FINAL_RESEARCH_REPORT.md
  independent_checks/exp1_inspection.txt
  independent_checks/sanity_checks.txt
  manifest.json
  order_map/all_orders_scored.jsonl
  order_map/config.json
  order_map/design.jsonl
  order_map/DIAGNOSTIC_ORDER.txt
  order_map/environment.json
  order_map/raw_generations.jsonl
  order_map/report.md
  order_map/report.txt
  order_map/scored_generations.jsonl
  order_map/scoring.txt
  order_map/summary.csv
  priority0/config.json
  priority0/design.jsonl
  priority0/environment.json
  priority0/raw_generations.jsonl
  priority0/report.md
  priority0/report.txt
  priority0/scored_generations.jsonl
  priority0/scoring.txt
  priority0/summary.csv
  priority_intervention/bridge/design.jsonl
  priority_intervention/bridge/raw_generations.jsonl
  priority_intervention/bridge/report.md
  priority_intervention/bridge/scored_generations.jsonl
  priority_intervention/main/design.jsonl
  priority_intervention/main/raw_generations.jsonl
  priority_intervention/main/report.txt
  priority_intervention/main/scored_generations.jsonl
  priority_intervention/main/scoring.txt
  priority_intervention/report.md
  priority_intervention/summary.csv
  RESEARCH_LOG.md
  seed_validation/config.json
  seed_validation/design.jsonl
  seed_validation/environment.json
  seed_validation/raw_generations.jsonl
  seed_validation/report.md
