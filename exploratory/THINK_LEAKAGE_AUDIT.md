# Reasoning-channel leakage: what the bug was, and what it did not touch

A defect was found in `vllm_backend/reasoning.py` during the backend
consolidation, in which a model's entire reasoning trace could be recorded as
its final answer, silently and with a successful outcome. This note exists so
that a later reader who sees the fix does not reasonably conclude that the
earlier Qwen3 results are contaminated.

**They are not. Every archived generation was audited row by row, and the
published estimates stand unchanged.**

## The bug

vLLM's `qwen3` reasoning parser finds the reasoning channel by looking for an
opening `<think>` marker in the model's output. Some chat templates **pre-open**
the block: they render `<|im_start|>assistant\n<think>\n`, so the opening marker
is in the PROMPT and never appears in the generation at all. The parser looks
for it, does not find it, concludes there was no reasoning, and returns the
whole trace as content.

Nothing about that failure is visible downstream. The row is well-formed, the
answer field is populated, and the outcome is `OK`. A sentence-count verifier
then scores a thousand tokens of scratchpad as though it were the answer.

Verified on this host, vLLM 0.15.1: all four probe rows on
`Qwen3-4B-Thinking-2507` contained `</think>` and no `<think>`, and the parser
assigned 100% of the reasoning text to the answer.

`split()` now repairs this, and only when the split provably failed — no
reasoning found while a close delimiter is present — so an answer that genuinely
had no reasoning is left alone.

## Which execution path was vulnerable

Only **single-generation parsing**: one `generate` call whose output is split
afterwards by a parser, on a checkpoint whose template pre-opens the block.

The archived reasoning runs did not use that path. They generated the two
channels as **separate calls** — a think phase stopped at the close delimiter,
then an answer phase from a fresh prompt — so the answer was never the output of
a split and could not inherit a trace. The vulnerability was introduced by the
consolidation's single-phase strategy and fixed before it produced any data.

Checkpoint behaviour, established by rendering the cached templates rather than
inferred:

| checkpoint | pre-opens `<think>` | used by |
|---|---|---|
| `Qwen/Qwen3-4B-Thinking-2507` | **yes** | probe only; no archived results |
| `Qwen/Qwen3-4B` | no | reasoning line, cross-model canonical |
| `Qwen/Qwen3-4B-Instruct-2507` | n/a — no reasoning channel | the exploratory ladder |

## What was audited

Every stored generation carrying a reasoning condition: **1,600 rows** across
three corpora.

| corpus | file | rows | marker-bearing answers |
|---|---|---|---|
| natural-reasoning endpoint | `natural_reasoning.jsonl` | 160 | **0** |
| capped reasoning ladder | `s18_reseeded.jsonl` | 800 | **1** |
| five-checkpoint cross-model | `ACTUAL_CROSS_MODEL_DCI_ROWS.jsonl` | 640 | **0** |

### Criteria

Two, because marker absence alone is not proof — a leak on a pre-opening
template produces a trace with *no* opening marker.

1. **Marker presence.** The answer field matched against `</?think>`,
   `◁/?think▷`, `<|channel>thought` and `<channel|>`.
2. **Empty-reasoning signature.** The shape a marker-free leak takes is a
   populated answer beside an *empty* reasoning field, with the answer far
   longer than the task calls for. Checked per checkpoint, with the answer
   length distribution beside it.

### Results of the second criterion

Every answered row on `Qwen3.5-4B`, `Qwen3.5-9B` and `Kimi-VL` carried a
non-empty reasoning field: the split worked. `gemma-4-E4B-it` had 5 answered
rows with an empty reasoning field, consistent with its independently measured
channel-validity rate of 0.975/0.963, and their answers are ordinary in length
rather than absorbed traces. Median answer length is 52–72 words against a
median *reasoning* length of 1,158 tokens in the natural corpus, so an absorbed
trace would be conspicuous. None is.

### The single marker-bearing row

`row_id 3fe8102d81a5be684c25`, capped ladder, budget **b = 256**, focal arm,
238 words, `reasoning_cap_hit=True`, `closed_naturally=False`.

The model was cut off mid-reasoning by the budget, so the answer phase continued
the scratchpad. This is truncation, not a parser failure, and it falls inside
the cap-bound regime the programme already refuses to interpret: `b = 256` is
cap-bound at 86% (bracket) and 94% (semicolon), which is why the "any thinking
at all" claim was withdrawn and cap-bound points are drawn hollow.

## Why the existing results remain usable

* **τ = +0.400 [+0.225, +0.551]**, the natural-reasoning semicolon result, rests
  on 160 rows with zero markers and zero empty-reasoning answers. Unaffected.
* The **bracket τ = +0.000** rests on the same corpus. Unaffected as an estimate
  — it remains `NOT_IDENTIFIED` for the separate reasons recorded in
  `SCIENTIFIC_CLAIM_AUDIT.md` §1.1, none of which is this bug.
* The **cross-model** cells are unaffected; their identification failures are
  target ceilings and focal non-uptake, again unrelated.
* The **capped ladder's** one affected row sits in a cell already excluded from
  interpretation, so no published estimate changes if it is dropped.

## Which future runs require the corrected backend

Any run that uses the `single_phase` strategy with a reasoning parser on a
checkpoint whose template pre-opens the reasoning block. That is the combination
the repair addresses, and it is the combination the cross-model line of work
uses, so the corrected backend is required for:

* any re-run of the cross-model design under `THINKING_ENABLED_BOUNDED`;
* any new checkpoint whose template pre-opens `<think>`, which must be
  established by rendering rather than assumed from the name;
* any use of `single_phase` on `Qwen3-4B-Thinking-2507`.

Runs using `two_phase_splice`, and any run on a checkpoint with no reasoning
channel, are not exposed to this defect by construction.

## Reproducing this audit

The raw generations are gitignored and live in the sibling worktrees. Both
criteria are a few lines over the stored rows; the corpora are identified by
content hash in `CANONICAL_RUN_MANIFEST.json` and
`ACTUAL_CROSS_MODEL_DCI_RUN_MANIFEST.json`, so an auditor can confirm they are
reading the same bytes this note describes.
