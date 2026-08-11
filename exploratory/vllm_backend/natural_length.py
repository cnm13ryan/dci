"""How long does this reasoning model actually think on the real DCI prompts?

Uses the REAL stored prompts from an executed run, so the distribution is the one
the experiment would face, not a distribution over toy questions.

Nothing is scored here. The single question is where `</think>` lands when the
budget is not binding, which decides whether a reasoning-budget grid can be
defined at all. The answer channel is kept separate from the first token.
"""
import json
import sys
from pathlib import Path

MODEL = sys.argv[1]
REVISION = sys.argv[2]
MAX_TOKENS = int(sys.argv[3]) if len(sys.argv) > 3 else 32768
OUT = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("natural_length.json")
PROMPTS = Path("nl_prompts.json")

THINK_CLOSE = "</think>"


def main():
    from vllm import LLM, SamplingParams

    records = json.loads(PROMPTS.read_text())
    llm = LLM(model=MODEL, revision=REVISION, dtype="bfloat16",
              tensor_parallel_size=2, gpu_memory_utilization=0.85,
              max_model_len=MAX_TOKENS + 2048, enforce_eager=True,
              disable_custom_all_reduce=True, seed=20260810)
    tok = llm.get_tokenizer()

    prompts = []
    for record in records:
        messages = []
        if record.get("system_message"):
            messages.append({"role": "system", "content": record["system_message"]})
        messages.append({"role": "user", "content": record["user_prompt"]})
        prompts.append(tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True))

    params = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=MAX_TOKENS,
                            seed=20260810)
    outputs = llm.generate(prompts, params)

    rows = []
    for record, out in zip(records, outputs):
        completion = out.outputs[0]
        text = completion.text
        closed = THINK_CLOSE in text
        if closed:
            reasoning, answer = text.split(THINK_CLOSE, 1)
        else:
            reasoning, answer = text, ""
        # Token-accurate reasoning length, not a character proxy.
        reasoning_tokens = len(tok.encode(reasoning, add_special_tokens=False))
        rows.append({
            "row_id": record.get("row_id"), "task_id": record.get("task_id"),
            "arm": record.get("arm"), "variant": record.get("variant"),
            "closed_naturally": closed,
            "reasoning_tokens": reasoning_tokens,
            "answer_chars": len(answer.strip()),
            "total_tokens": len(completion.token_ids),
            "finish_reason": completion.finish_reason,
            "cap_hit": completion.finish_reason == "length",
            "answer_preview": answer.strip()[:300],
        })
    OUT.write_text(json.dumps(rows, indent=1))

    closed = [r for r in rows if r["closed_naturally"]]
    lengths = sorted(r["reasoning_tokens"] for r in closed)
    print(f"\nmodel={MODEL} max_tokens={MAX_TOKENS} n={len(rows)}")
    print(f"natural closure: {len(closed)}/{len(rows)} = {len(closed)/len(rows):.3f}")
    if lengths:
        def pct(p):
            return lengths[min(len(lengths) - 1, int(p * len(lengths)))]
        print(f"reasoning tokens among closed: min={lengths[0]} p25={pct(.25)} "
              f"median={pct(.5)} p75={pct(.75)} p90={pct(.9)} max={lengths[-1]}")
    print("answers non-empty:", sum(1 for r in rows if r["answer_chars"] > 0),
          "/", len(rows))


if __name__ == "__main__":
    main()
