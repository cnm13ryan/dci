# Natural reasoning: the canonical result

Every number here is produced by `natural_analysis.py` from the frozen raw
generations, scored through the same registry, and fails loudly if any guard
breaks. Regenerate with `uv run python natural_analysis.py`.

## Main result

Two prompts differ by one phrase — *"use exactly 1 pair of round brackets"*
against *"use exactly 1 semicolon"*. In every other respect they are identical:
same task, same main instruction, same competing instruction, same model, same
decoding.

When the model is stopped after a fixed number of reasoning tokens, both prompts
show the same broad pattern seen earlier. When it is instead **allowed to finish
thinking on its own**, the bracket prompt's conflict is gone completely — the
competing instruction causes **exactly zero** extra failures on "write exactly 4
sentences", in all 20 tasks — while the semicolon prompt still costs
**+0.400 [+0.225, +0.551]**, roughly a 40 percentage-point increase in failure.

Letting the model think as long as it likes does not make it a reliable
instruction-follower. It makes it reliable in one prompt context and leaves it
unreliable in a context that differs by a single word.

## Experimental conditions

| | |
|---|---|
| model | `Qwen/Qwen3-4B` @ `1cfa9a7208912126459214e8b04321603b3df60c`, a reasoning model |
| backend | vLLM 0.15.1+rocm720, tensor-parallel 2, bf16, T = 0.7, top-p 0.9 |
| main instruction (scored) | *"Write exactly 4 sentences."* |
| competing instruction | *"Make each sentence strictly longer than the preceding sentence."* |
| matched comparison | *"Begin every sentence with a word whose first letter is S."* |
| formatting instruction, version 1 | *"Use exactly 1 pair of round brackets in the whole answer, and place it wherever you judge best."* |
| formatting instruction, version 2 | *"Use exactly 1 semicolon in the whole answer, and place it wherever you judge best."* |
| design | instruction order QAC, three instructions per prompt, 20 pilot tasks × 2 replicates × 2 arms × 2 backgrounds = 160 answers |
| answer allowance | 512 tokens, identical in every condition |
| **natural reasoning** | the experiment did not stop the model's reasoning. The only bound is an engineering ceiling of **39,550** tokens, derived from the context envelope, and **0/160 rows reached it**. |

**"Natural" means only that the experiment did not stop the reasoning.** It does
not mean unlimited compute, unlimited context, or maximum capability.

## How much reasoning the model chose to use

| background | arm | n | median | p25 | p75 | p90 | p95 | max | closed naturally | ceiling hits |
|---|---|---|---|---|---|---|---|---|---|---|
| + one bracket pair | competing | 40 | 549 | 381 | 656 | 843 | 1,200 | 1,570 | 1.000 | 0 |
| + one bracket pair | comparison | 40 | 353 | 271 | 499 | 707 | 898 | 1,985 | 1.000 | 0 |
| **+ one semicolon** | **competing** | 40 | **719** | 552 | 1,197 | 1,669 | 2,442 | **5,888** | 1.000 | 0 |
| + one semicolon | comparison | 40 | 425 | 345 | 789 | 1,770 | 2,153 | 2,278 | 1.000 | 0 |

The semicolon condition **reasons longer** — median 719 against 549 in the
competing arm, with a far heavier tail — and still fails more.

This is a **descriptive, post-treatment** difference. Realised reasoning length is
chosen by the model, not assigned. It is not evidence that longer reasoning
causes the failure, and no mediation is claimed. Increased difficulty,
unsuccessful repair attempts, a different planning strategy, and conflict
detected but not resolved all remain live and untested explanations.

## What the model actually did when the instructions competed

Shares of answers in the competing-instruction arm, under natural reasoning:

| background | both satisfied | main instruction only | competing only | neither |
|---|---|---|---|---|
| + one bracket pair | 0.075 | **0.925** | 0.000 | 0.000 |
| + one semicolon | 0.050 | 0.450 | 0.050 | **0.450** |

**This is the most interpretively important table in the branch.** Unlimited
thinking does not make the model satisfy both instructions — "both satisfied"
reaches only 7.5% even in the repaired condition. What additional reasoning buys
is that the model **protects the main instruction and sacrifices the competing
one**. Under the semicolon instruction it does not manage even that: 45% of
answers satisfy neither.

An independently verified satisfiability certificate exists showing that all
constraints in this design *can* be satisfied simultaneously, so "neither" is a
failure of the model, not of the task.

## Robustness

| check | result |
|---|---|
| independent sampling | 0/80 natural and 0/400 capped replicate pairs identical, against 390/400 before the seed fix |
| task heterogeneity | 14 of 20 tasks positive, 5 exactly zero, 1 negative (range −0.500 to +1.000) |
| **leave one task out** | semicolon estimate ranges **+0.368 to +0.447** over all 20 refits; **the sign never changes** |
| **long-trace sensitivity** | dropping the longest trace, the longest 5%, or the longest 10% of each arm gives +0.425, +0.400, +0.472 — the result is **not** carried by the tail; the 10% row keeps 19 bracket and 18 semicolon tasks, so it is not the same task set as the others ([SCIENTIFIC_CLAIM_AUDIT.md §1.5](SCIENTIFIC_CLAIM_AUDIT.md#15-long-trace-robustness-table--supported_with_narrower_wording)) |
| ceiling | 0/160 reached the 39,550-token engineering ceiling |
| answer integrity | 0 empty, 0 truncated, mean 119 answer tokens |
| **leakage** | 2/160 detector hits, **both inspected, both benign** — ordinary prose using the word *wait*. Confirmed leakage **0/160**. |

The bracket condition is 0.000 in *every* task, so its leave-one-out range is
degenerate at 0.000 — the null is not an average over a mixture.

## What this supports

* For this model and this instruction pair, allowing unrestricted reasoning
  removes the extra main-instruction failures in the bracket condition and leaves
  a substantial increase in the semicolon condition.
* The natural endpoint is genuine: nothing was stopped, and nothing came near the
  ceiling.
* The aggregate is not an artifact of a few tasks or a few very long traces.
* Additional reasoning changes **which** instruction survives, more than whether
  both do.

## What this does NOT establish

* **Not a claim about models in general.** One checkpoint, one instruction pair,
  20 tasks.
* **Not a claim that semicolons universally cause interference.** The mechanism is
  unidentified; that work belongs to the original experimental branch.
* **Not causal evidence that longer realised reasoning causes the failure.**
  Reasoning length is post-treatment and is reported descriptively only.
* **Not proof that no inference-time method could solve this conflict.** Only one
  family of reasoning-budget interventions was tested.
* **Nothing about the shape of the semicolon curve.** Its capped points bounce
  between +0.325 and +0.625 with intervals near ±0.2, and adjacent settings are
  not resolved. The supported claim is **persistence**, not trend, threshold or
  turning point.

## An honest tension worth stating

Natural reasoning has a median of 511 tokens — essentially the 512-token setting
— yet the semicolon estimate is +0.400 at natural against +0.625 at 512. Two
things differ, and this design cannot separate them: the 512 setting **cut short
60% of its rows**, so its realised distribution is truncated where natural's runs
on to 5,888; and the two intervals overlap substantially, so part of the gap may
simply be noise. The figure does not assert that natural reasoning is better than
512, and neither does this document.

## Open questions, owned elsewhere

These belong to the original experimental worktree and were deliberately not
started here: what property of the semicolon instruction produces the effect;
whether other marks behave the same way; whether the effect survives other
instruction orders, higher compositional load, or other model families.
