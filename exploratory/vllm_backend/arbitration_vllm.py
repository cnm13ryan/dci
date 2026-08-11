"""Two-phase reasoning generation with a SCIENTIFIC seed per (task, replicate).

Why this file exists separately from `reasoning_vllm.py`
-------------------------------------------------------
`reasoning_vllm.py` seeds a request from its **index in the design file**:

    seed = MASTER + offset + 7919 * row_index

That is distinct per row, so it repaired the original "one seed per batch" bug.
It is still not a *scientific* seed, because the index is a property of the file,
not of the experimental unit. Two matched rows -- the same task and replicate in
the focal arm and in the reference arm -- get different seeds, so the paired
contrast tau is taken across independent decoder noise instead of common random
numbers, and a design change that reorders rows silently reseeds every unit.

Here the seed is a pure function of the experimental unit:

    seed = blake2b(MASTER_SEED | task_id | replicate | phase)

so that

  1. different replicates of one task get different seeds;
  2. the same (task_id, replicate) gets the SAME seed in every condition that is
     paired with it -- arm, background, order and reasoning budget all reuse it,
     which makes tau and Delta common-random-number differences;
  3. a retry, a re-run, or a reordered design file reproduces the same seed;
  4. the integer actually handed to the engine is written into every record.

The two phases are seeded apart, so the answer phase never inherits the thinking
phase's stream.

Nothing is scored here. Scoring runs in the study venv against the same registry,
from the answer field only; the reasoning channel never reaches a verifier.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

MODEL = sys.argv[1]
REVISION = sys.argv[2]
BUDGETS = [int(b) for b in sys.argv[3].split(",")]
DESIGN = Path(sys.argv[4])
OUT = Path(sys.argv[5])
ANSWER_TOKENS = int(sys.argv[6])
MASTER_SEED = int(sys.argv[7])
EXPERIMENT_ID = sys.argv[8]

THINK_CLOSE = "</think>"
TEMPERATURE = 0.7
TOP_P = 0.9
#: vLLM's sampler takes a uint64 but the reproducible range that round-trips
#: through the request metadata is the non-negative int32 range.
SEED_MODULUS = 2 ** 31 - 1


def scientific_seed(task_id: str, replicate: int, phase: str) -> int:
    """A seed determined by the experimental unit, not by file position."""
    key = f"{MASTER_SEED}|{task_id}|{replicate}|{phase}".encode()
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(),
                          "big") % SEED_MODULUS


def main():
    from vllm import LLM, SamplingParams

    rows = [json.loads(line) for line in DESIGN.open()]
    llm = LLM(model=MODEL, revision=REVISION, dtype="bfloat16",
              tensor_parallel_size=2, gpu_memory_utilization=0.85,
              max_model_len=16384, enforce_eager=True,
              disable_custom_all_reduce=True, seed=MASTER_SEED)
    tok = llm.get_tokenizer()

    def render(row, thinking: bool) -> str:
        messages = []
        if row.get("system_message"):
            messages.append({"role": "system", "content": row["system_message"]})
        messages.append({"role": "user", "content": row["user_prompt"]})
        return tok.apply_chat_template(messages, tokenize=False,
                                       add_generation_prompt=True,
                                       enable_thinking=thinking)

    def seeds(phase: str) -> list[int]:
        return [scientific_seed(r["task_id"], r["replicate"], phase)
                for r in rows]

    def latency_of(out) -> float | None:
        metrics = getattr(out, "metrics", None)
        if metrics is None:
            return None
        finished = getattr(metrics, "finished_time", None)
        arrived = getattr(metrics, "arrival_time", None)
        if finished is None or arrived is None:
            return None
        return float(finished - arrived)

    def base(row, budget, prompt, think_seed, answer_seed) -> dict:
        return dict(row, experiment_id=EXPERIMENT_ID, model_id=MODEL,
                    model_revision=REVISION, reasoning_budget=budget,
                    replicate_id=row["replicate"], background=row["variant"],
                    exact_prompt=prompt, temperature=TEMPERATURE, top_p=TOP_P,
                    master_seed=MASTER_SEED,
                    reasoning_request_seed=think_seed,
                    actual_request_seed=answer_seed,
                    answer_token_budget=ANSWER_TOKENS)

    records = []
    for budget in BUDGETS:
        started = time.perf_counter()
        answer_seeds = seeds("answer")
        if budget == 0:
            # The model's own non-thinking mode. Not a zero-length truncation.
            prompts = [render(row, False) for row in rows]
            outs = llm.generate(prompts, [SamplingParams(
                temperature=TEMPERATURE, top_p=TOP_P, max_tokens=ANSWER_TOKENS,
                seed=s) for s in answer_seeds])
            for row, prompt, seed, out in zip(rows, prompts, answer_seeds, outs):
                done = out.outputs[0]
                records.append(dict(
                    base(row, 0, prompt, None, seed),
                    raw_reasoning="", reasoning_tokens=0, closed_naturally=True,
                    reasoning_cap_hit=False,
                    raw_final_answer=done.text.strip(),
                    final_tokens=len(done.token_ids),
                    truncated=done.finish_reason == "length",
                    native_nonthinking=True, latency=latency_of(out),
                    technical_failure=not done.text.strip()))
        else:
            think_seeds = seeds("think")
            prompts = [render(row, True) for row in rows]
            think = llm.generate(prompts, [SamplingParams(
                temperature=TEMPERATURE, top_p=TOP_P, max_tokens=budget, seed=s,
                stop=[THINK_CLOSE], include_stop_str_in_output=False)
                for s in think_seeds])
            continued, meta = [], []
            for prompt, out in zip(prompts, think):
                done = out.outputs[0]
                continued.append(f"{prompt}{done.text}{THINK_CLOSE}\n\n")
                meta.append((done.text, len(done.token_ids),
                             done.finish_reason == "stop", latency_of(out)))
            answers = llm.generate(continued, [SamplingParams(
                temperature=TEMPERATURE, top_p=TOP_P, max_tokens=ANSWER_TOKENS,
                seed=s) for s in answer_seeds])
            for row, prompt, tseed, aseed, (reasoning, n, closed, tlat), out in zip(
                    rows, prompts, think_seeds, answer_seeds, meta, answers):
                done = out.outputs[0]
                alat = latency_of(out)
                records.append(dict(
                    base(row, budget, prompt, tseed, aseed),
                    raw_reasoning=reasoning, reasoning_tokens=n,
                    closed_naturally=closed, reasoning_cap_hit=not closed,
                    raw_final_answer=done.text.strip(),
                    final_tokens=len(done.token_ids),
                    truncated=done.finish_reason == "length",
                    native_nonthinking=False,
                    latency=None if (tlat is None or alat is None) else tlat + alat,
                    technical_failure=not done.text.strip()))
        elapsed = time.perf_counter() - started
        cell = [r for r in records if r["reasoning_budget"] == budget]
        print(f"b={budget:>5}  {len(cell)} rows  {elapsed:6.1f}s  "
              f"closed={sum(r['closed_naturally'] for r in cell)/len(cell):.3f}  "
              f"mean_reasoning={sum(r['reasoning_tokens'] for r in cell)/len(cell):7.1f}  "
              f"failures={sum(r['technical_failure'] for r in cell)}  "
              f"truncated={sum(r['truncated'] for r in cell)}", flush=True)

    with OUT.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    print("wrote", OUT, len(records), "records")


if __name__ == "__main__":
    main()
