"""The NATURAL_REASONING condition: let the model finish thinking on its own.

Every other reasoning condition in this study deliberately caps the thinking
phase. This one does not. The only limit is an engineering ceiling derived from
what actually fits in the context window, and the run is only valid if that
ceiling is never reached:

    ceiling = context_limit
              - longest_rendered_prompt
              - answer_allowance          (identical to every other condition)
              - control_tokens            (the `</think>` splice)
              - safety_margin             (2% of the context window)

The number is whatever that arithmetic gives. It is deliberately NOT a round
power of two: a round number would be a guess about how much room is enough,
and the requirement here is a limit derived from the envelope that the model
almost never touches.

"Natural" means only this: the experiment did not stop the model's reasoning
before it finished. It does not mean unlimited compute or unlimited context.
"""
import json
import math
import sys
import time
from pathlib import Path

MODEL = sys.argv[1]
REVISION = sys.argv[2]
DESIGN = Path(sys.argv[3])
OUT = Path(sys.argv[4])
ANSWER_TOKENS = int(sys.argv[5]) if len(sys.argv) > 5 else 512

THINK_CLOSE = "</think>"
CONTEXT_LIMIT = 40960          # Qwen3-4B max_position_embeddings, read from config
SAFETY_FRACTION = 0.02         # reserve 2% of the window rather than trust the edge
#: Offset that keeps this condition's seeds disjoint from every other run.
SEED_OFFSET = 90000


def main():
    from vllm import LLM, SamplingParams

    rows = [json.loads(line) for line in DESIGN.open()]
    llm = LLM(model=MODEL, revision=REVISION, dtype="bfloat16",
              tensor_parallel_size=2, gpu_memory_utilization=0.85,
              max_model_len=CONTEXT_LIMIT, enforce_eager=True,
              disable_custom_all_reduce=True, seed=20260810)
    tok = llm.get_tokenizer()

    prompts = []
    for row in rows:
        messages = []
        if row.get("system_message"):
            messages.append({"role": "system", "content": row["system_message"]})
        messages.append({"role": "user", "content": row["user_prompt"]})
        prompts.append(tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=True))

    prompt_tokens = [len(tok.encode(p, add_special_tokens=False)) for p in prompts]
    longest_prompt = max(prompt_tokens)
    control_tokens = len(tok.encode(f"{THINK_CLOSE}\n\n", add_special_tokens=False))
    safety = math.ceil(CONTEXT_LIMIT * SAFETY_FRACTION)
    ceiling = CONTEXT_LIMIT - longest_prompt - ANSWER_TOKENS - control_tokens - safety

    envelope = {"context_limit": CONTEXT_LIMIT, "longest_prompt_tokens": longest_prompt,
                "median_prompt_tokens": sorted(prompt_tokens)[len(prompt_tokens) // 2],
                "answer_allowance": ANSWER_TOKENS, "control_tokens": control_tokens,
                "safety_margin": safety, "derived_ceiling": ceiling}
    print("engineering envelope:", json.dumps(envelope), flush=True)

    # One seed PER ROW. A single shared seed makes two replicate rows of the same
    # task byte-identical, so "2 replicates" silently becomes one draw counted
    # twice. Same convention as the fixed `reasoning_vllm.py`.
    def seeds(offset: int) -> list[int]:
        return [20260810 + offset + 7919 * i for i in range(len(prompts))]

    started = time.perf_counter()
    think = llm.generate(prompts, [SamplingParams(
        temperature=0.7, top_p=0.9, max_tokens=ceiling, seed=s,
        stop=[THINK_CLOSE], include_stop_str_in_output=False)
        for s in seeds(SEED_OFFSET)])
    think_seconds = time.perf_counter() - started

    continued, meta = [], []
    for prompt, out in zip(prompts, think):
        completion = out.outputs[0]
        closed = completion.finish_reason == "stop"
        continued.append(f"{prompt}{completion.text}{THINK_CLOSE}\n\n")
        meta.append((completion.text, len(completion.token_ids), closed))

    started = time.perf_counter()
    answers = llm.generate(continued, [SamplingParams(
        temperature=0.7, top_p=0.9, max_tokens=ANSWER_TOKENS, seed=s)
        for s in seeds(SEED_OFFSET + 1)])
    answer_seconds = time.perf_counter() - started

    records = []
    for row, (reasoning, n_tokens, closed), out in zip(rows, meta, answers):
        completion = out.outputs[0]
        records.append(dict(
            row, condition="NATURAL_REASONING", reasoning_budget=ceiling,
            engineering_ceiling=ceiling, reasoning=reasoning,
            reasoning_tokens=n_tokens, closed_naturally=closed,
            reasoning_cap_hit=not closed, answer=completion.text.strip(),
            answer_tokens=len(completion.token_ids),
            answer_truncated=completion.finish_reason == "length",
            native_nonthinking=False))

    with OUT.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    (OUT.with_name(OUT.stem + "_envelope.json")).write_text(json.dumps(
        {**envelope, "reasoning_phase_seconds": think_seconds,
         "answer_phase_seconds": answer_seconds, "rows": len(records),
         "cap_hits": sum(r["reasoning_cap_hit"] for r in records)}, indent=1))

    lengths = sorted(r["reasoning_tokens"] for r in records)
    caps = sum(r["reasoning_cap_hit"] for r in records)

    def pct(p):
        return lengths[min(len(lengths) - 1, int(p * len(lengths)))]

    print(f"\nNATURAL_REASONING · {len(records)} rows · ceiling {ceiling}")
    print(f"  reached the ceiling: {caps}/{len(records)}"
          f"{'  <-- INVALID, the ceiling binds' if caps else '  (none — the ceiling never binds)'}")
    print(f"  reasoning tokens: min {lengths[0]} · p25 {pct(.25)} · median {pct(.5)} "
          f"· p75 {pct(.75)} · p90 {pct(.9)} · max {lengths[-1]}")
    print(f"  empty answers: {sum(1 for r in records if not r['answer'])} · "
          f"truncated: {sum(r['answer_truncated'] for r in records)}")
    print(f"  reasoning phase {think_seconds:.1f}s · answer phase {answer_seconds:.1f}s")
    return 1 if caps else 0


if __name__ == "__main__":
    raise SystemExit(main())
