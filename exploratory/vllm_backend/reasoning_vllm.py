"""Two-phase reasoning-budget generation on vLLM, channels kept apart.

The reasoning channel is NEVER part of the response. Phase 1 thinks under the
assigned budget `b`; phase 2 answers under a budget that is identical in every
treatment, so the verifier sees a comparable surface at every b.

`b = 0` is the model's OWN non-thinking mode (`enable_thinking=False`), not a
zero-length truncation — that makes the bottom of the grid a native condition
rather than an interruption.

Nothing is scored here. Scoring happens in the study venv against the registry,
from the saved answer field.
"""
import json
import sys
import time
from pathlib import Path

MODEL = sys.argv[1]
REVISION = sys.argv[2]
BUDGETS = [int(b) for b in sys.argv[3].split(",")]
DESIGN = Path(sys.argv[4])
OUT = Path(sys.argv[5])
ANSWER_TOKENS = int(sys.argv[6]) if len(sys.argv) > 6 else 512

THINK_CLOSE = "</think>"


def main():
    from vllm import LLM, SamplingParams

    rows = [json.loads(line) for line in DESIGN.open()]
    llm = LLM(model=MODEL, revision=REVISION, dtype="bfloat16",
              tensor_parallel_size=2, gpu_memory_utilization=0.85,
              max_model_len=16384, enforce_eager=True,
              disable_custom_all_reduce=True, seed=20260810)
    tok = llm.get_tokenizer()

    def render(row, thinking: bool) -> str:
        messages = []
        if row.get("system_message"):
            messages.append({"role": "system", "content": row["system_message"]})
        messages.append({"role": "user", "content": row["user_prompt"]})
        return tok.apply_chat_template(messages, tokenize=False,
                                       add_generation_prompt=True,
                                       enable_thinking=thinking)

    records = []
    for budget in BUDGETS:
        started = time.perf_counter()
        if budget == 0:
            # Native non-thinking mode: one generation, fixed answer budget.
            prompts = [render(row, False) for row in rows]
            outs = llm.generate(prompts, SamplingParams(
                temperature=0.7, top_p=0.9, max_tokens=ANSWER_TOKENS, seed=20260810))
            for row, out in zip(rows, outs):
                completion = out.outputs[0]
                records.append(dict(row, reasoning_budget=0, reasoning="",
                                    reasoning_tokens=0, closed_naturally=True,
                                    reasoning_cap_hit=False,
                                    answer=completion.text.strip(),
                                    answer_tokens=len(completion.token_ids),
                                    answer_truncated=completion.finish_reason == "length",
                                    native_nonthinking=True))
        else:
            prompts = [render(row, True) for row in rows]
            think = llm.generate(prompts, SamplingParams(
                temperature=0.7, top_p=0.9, max_tokens=budget, seed=20260810,
                stop=[THINK_CLOSE], include_stop_str_in_output=False))
            continued, meta = [], []
            for prompt, out in zip(prompts, think):
                completion = out.outputs[0]
                closed = completion.finish_reason == "stop"
                continued.append(f"{prompt}{completion.text}{THINK_CLOSE}\n\n")
                meta.append((completion.text, len(completion.token_ids), closed))
            answers = llm.generate(continued, SamplingParams(
                temperature=0.7, top_p=0.9, max_tokens=ANSWER_TOKENS,
                seed=20260811))
            for row, (reasoning, n_tokens, closed), out in zip(rows, meta, answers):
                completion = out.outputs[0]
                records.append(dict(row, reasoning_budget=budget,
                                    reasoning=reasoning, reasoning_tokens=n_tokens,
                                    closed_naturally=closed,
                                    reasoning_cap_hit=not closed,
                                    answer=completion.text.strip(),
                                    answer_tokens=len(completion.token_ids),
                                    answer_truncated=completion.finish_reason == "length",
                                    native_nonthinking=False))
        elapsed = time.perf_counter() - started
        done = [r for r in records if r["reasoning_budget"] == budget]
        print(f"b={budget:>5}  {len(done)} rows  {elapsed:6.1f}s  "
              f"closed={sum(r['closed_naturally'] for r in done)/len(done):.3f}  "
              f"mean_reasoning={sum(r['reasoning_tokens'] for r in done)/len(done):7.1f}  "
              f"empty_answers={sum(1 for r in done if not r['answer'])}  "
              f"truncated={sum(r['answer_truncated'] for r in done)}", flush=True)

    with OUT.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    print("wrote", OUT, len(records), "records")


if __name__ == "__main__":
    main()
