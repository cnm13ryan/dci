"""Diagnose Qwen3.5 reasoning termination one request at a time. Backend venv.

Concurrency 1, four DCI-shaped prompts, full per-request accounting. The point
is to separate causes that the earlier batched runs could not distinguish:

* genuine reasoning loops (the model repeats itself and never converges);
* a heavy tail (it does terminate, but far out);
* wrong stop-token handling (it emits the close marker and vLLM ignores it);
* parser failure (it closes and the parser fails to see it);
* chat-template mismatch (thinking never actually enabled);
* head-of-line blocking (a batching artefact, not a model property).

Head-of-line blocking is ruled out by construction here: one request at a time.
The last ~1,000 reasoning characters of every non-terminating run are saved so a
loop can be recognised by eye, and a cheap repetition statistic is computed.

    python crossmodel/vllm_qwen_probe.py --model Qwen/Qwen3.5-4B \
        --revision <sha> --max-model-len 40960 --out runs/DIR/probe.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from dataclasses import replace as _replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vllm_backend import engine as _engine
from vllm_backend.hardware import probe as _probe_host
from vllm_backend.reasoning import build_parser as _build_parser
from vllm_backend.registry import get_or_default
from vllm_backend.resolve import resolve_engine, resolve_sampling

SYSTEM = ("Produce only the requested answer. Do not discuss, restate, "
          "enumerate, or explain the constraints or your planning process.")

#: The frozen QAC shape, two backgrounds x two arms, on one topic.
TOPIC = "Explain how a corkscrew removes a cork."
A = "Write exactly 4 sentences."
B = ("Make each sentence strictly longer than the preceding sentence when "
     "measured by word count.")
R = "Begin every sentence with a word whose first letter is S."
SEMI = ("Use exactly 1 semicolon in the whole answer, and place it wherever "
        "you judge best.")
PAREN = ("Use exactly 1 pair of round brackets in the whole answer, and place "
         "it wherever you judge best.")


def prompt(arm: str, background: str) -> str:
    return (f"{TOPIC}\n\nSatisfy every constraint below simultaneously:\n"
            f"1. {arm}\n2. {A}\n3. {background}")


CASES = [
    ("focal|semicolon", prompt(B, SEMI)),
    ("reference|semicolon", prompt(R, SEMI)),
    ("focal|control", prompt(B, PAREN)),
    ("reference|control", prompt(R, PAREN)),
]


def repetition_score(text: str) -> dict:
    """Cheap loop detector: how concentrated are the trailing lines?"""
    tail = text[-6000:]
    lines = [l.strip() for l in tail.splitlines() if len(l.strip()) > 20]
    if not lines:
        return {"lines": 0, "distinct": 0, "top_line_share": 0.0}
    counts = Counter(lines)
    return {"lines": len(lines), "distinct": len(counts),
            "top_line_share": round(counts.most_common(1)[0][1] / len(lines), 3),
            "most_common": counts.most_common(1)[0][0][:160]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--max-model-len", type=int, default=40960)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    card = _replace(get_or_default(args.model), model_id=args.model)
    plan = resolve_engine(card, _probe_host(), {
        "tensor_parallel_size": 2, "max_model_len": args.max_model_len,
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "seed": 20260812, "model_revision": args.revision})
    llm, tokenizer, _load_seconds = _engine.build_engine(plan)
    reasoning_parser, _parser_label = _build_parser(
        card.reasoning_parser or "qwen3", tokenizer,
        card.think_open, card.think_close)

    # -- verify the reasoning interface is actually on -----------------------
    rendered_on = tokenizer.apply_chat_template(
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": CASES[0][1]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=True)
    rendered_off = tokenizer.apply_chat_template(
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": CASES[0][1]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    interface = {
        "enable_thinking_true_tail": rendered_on[-120:],
        "enable_thinking_false_tail": rendered_off[-120:],
        "template_actually_differs": rendered_on != rendered_off,
        "think_open_token_ids": tokenizer.encode("<think>",
                                                 add_special_tokens=False),
        "think_close_token_ids": tokenizer.encode("</think>",
                                                  add_special_tokens=False),
        "eos_token_id": tokenizer.eos_token_id,
        "parser": "qwen3",
    }
    print(json.dumps(interface, indent=1), flush=True)

    records = []
    for label, text in CASES:
        rendered = tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": text}],
            tokenize=False, add_generation_prompt=True, enable_thinking=True)
        prompt_tokens = len(tokenizer.encode(rendered, add_special_tokens=False))
        budget = args.max_model_len - prompt_tokens - 64
        started = time.perf_counter()
        # Concurrency 1: one prompt per generate call, so nothing this request
        # does can be blamed on another request in the batch.
        output = llm.generate([rendered], _engine.build_sampling(
            resolve_sampling(max_tokens=budget), budget, 11))[0]
        elapsed = time.perf_counter() - started
        completion = output.outputs[0]
        raw = completion.text
        try:
            reasoning, answer = reasoning_parser.extract_reasoning(raw, None)
        except Exception as error:
            reasoning, answer = None, f"<PARSER FAILED: {error}>"

        closed = "</think>" in raw
        n = len(completion.token_ids)
        record = {
            "case": label,
            "prompt_tokens": prompt_tokens,
            "max_tokens_allowed": budget,
            "generated_tokens": n,
            "hit_cap": completion.finish_reason == "length",
            "finish_reason": completion.finish_reason,
            "stop_reason": str(completion.stop_reason),
            "close_marker_in_raw": closed,
            "reasoning_chars": len(reasoning or ""),
            "answer_chars": len((answer or "").strip()),
            "answer": (answer or "").strip()[:400],
            "elapsed_seconds": round(elapsed, 1),
            "tokens_per_second": round(n / max(elapsed, 1e-6), 1),
            "repetition": repetition_score(reasoning or raw),
            "reasoning_tail_1000": (reasoning or raw)[-1000:],
        }
        records.append(record)
        print(f"\n[{label}] tokens={n} cap={record['hit_cap']} "
              f"closed={closed} answer_chars={record['answer_chars']} "
              f"{record['elapsed_seconds']}s "
              f"{record['tokens_per_second']} tok/s "
              f"top_line_share={record['repetition']['top_line_share']}",
              flush=True)
        Path(args.out).write_text(json.dumps(
            {"model": args.model, "revision": args.revision,
             "max_model_len": args.max_model_len,
             "interface": interface, "cases": records}, indent=1))

    Path(args.out).write_text(json.dumps(
        {"model": args.model, "revision": args.revision,
         "max_model_len": args.max_model_len,
         "interface": interface, "cases": records}, indent=1))
    closed_count = sum(1 for r in records if r["close_marker_in_raw"])
    print(f"\nclosed {closed_count}/{len(records)}; wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
