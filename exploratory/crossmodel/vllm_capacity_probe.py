"""Capacity search for one checkpoint under BF16 vLLM TP=2. Backend venv only.

Walks `max_model_len` downward (and `gpu_memory_utilization` across a small
grid), stopping at the first envelope that both loads AND generates. For each
attempt it records what actually happened to memory, because "it OOMed" is not
a measurement and the point here is to find the smallest envelope that
comfortably covers a DCI prompt plus its natural reasoning.

No quantization is tried at any point. The dual-GPU condition exists to supply
capacity; a quantized run would be a different numerical experiment.

    python crossmodel/vllm_capacity_probe.py --model <id> --revision <sha> \
        --out runs/DIR/capacity.json
"""
from __future__ import annotations

import argparse
import gc
import json
import subprocess
import time
import traceback
from pathlib import Path

SYSTEM = ("Produce only the requested answer. Do not discuss, restate, "
          "enumerate, or explain the constraints or your planning process.")

TRIVIAL = "Name the capital city of Japan."

#: The real DCI shape: focal, target, background, in the frozen QAC order.
DCI_SHAPED = (
    "Explain how a corkscrew removes a cork.\n\n"
    "Satisfy every constraint below simultaneously:\n"
    "1. Make each sentence strictly longer than the preceding sentence when "
    "measured by word count.\n"
    "2. Write exactly 4 sentences.\n"
    "3. Use exactly 1 semicolon in the whole answer, and place it wherever "
    "you judge best.")


def free_vram() -> list[float]:
    import torch

    return [round(torch.cuda.mem_get_info(i)[0] / 2 ** 30, 2)
            for i in range(torch.cuda.device_count())]


def attempt(model: str, revision: str, max_len: int, util: float,
            trust: bool, mm_limit: dict, think_open: str, think_close: str,
            template_kwargs: dict, parser_name: str | None) -> dict:
    """One (max_model_len, gpu_memory_utilization) attempt, fully reported."""
    from vllm import LLM, SamplingParams

    record: dict = {"max_model_len": max_len, "gpu_memory_utilization": util,
                    "free_vram_before": free_vram()}
    started = time.perf_counter()
    llm = None
    try:
        llm = LLM(model=model, revision=revision, dtype="bfloat16",
                  tensor_parallel_size=2, max_model_len=max_len,
                  gpu_memory_utilization=util,
                  disable_custom_all_reduce=True, enforce_eager=True,
                  trust_remote_code=trust, limit_mm_per_prompt=mm_limit,
                  seed=20260812)
        record["load_seconds"] = round(time.perf_counter() - started, 1)
        record["free_vram_after_load"] = free_vram()
        record["loaded"] = True

        tokenizer = llm.get_tokenizer()
        prompts = []
        for text in (TRIVIAL, DCI_SHAPED):
            prompts.append(tokenizer.apply_chat_template(
                [{"role": "system", "content": SYSTEM},
                 {"role": "user", "content": text}],
                tokenize=False, add_generation_prompt=True, **template_kwargs))
        record["prompt_tokens"] = [
            len(tokenizer.encode(p, add_special_tokens=False)) for p in prompts]

        # Leave the answer room the contract asks for; the rest is reasoning.
        budget = max_len - max(record["prompt_tokens"]) - 64
        sampling = SamplingParams(temperature=0.7, top_p=0.9, top_k=-1,
                                  max_tokens=budget, seed=11)
        started = time.perf_counter()
        outputs = llm.generate(prompts, sampling)
        record["generate_seconds"] = round(time.perf_counter() - started, 1)
        record["free_vram_after_generate"] = free_vram()

        parser = None
        if parser_name:
            from vllm.reasoning import ReasoningParserManager
            parser = ReasoningParserManager.get_reasoning_parser(
                parser_name)(tokenizer)

        results = []
        for label, output in zip(("trivial", "dci_shaped"), outputs):
            completion = output.outputs[0]
            text = completion.text
            if parser is not None:
                try:
                    reasoning, answer = parser.extract_reasoning(text, None)
                except Exception:                       # noqa: BLE001
                    reasoning, answer = None, None
            else:
                reasoning, answer = None, None
            if reasoning is None and answer is None:
                if think_close in text:
                    head, _, tail = text.partition(think_close)
                    lead, _, reasoning = head.partition(think_open) \
                        if think_open in head else ("", "", head)
                    answer = f"{lead.strip()}\n{tail.strip()}".strip()
                else:
                    reasoning, answer = ("", text.strip())
            results.append({
                "which": label,
                "finish_reason": completion.finish_reason,
                "generated_tokens": len(completion.token_ids),
                "reasoning_chars": len(reasoning or ""),
                "answer_chars": len((answer or "").strip()),
                "closed": think_close in text,
                "answer_head": (answer or "")[:200],
                "reasoning_head": (reasoning or "")[:200],
            })
        record["generations"] = results
        record["ok"] = all(r["answer_chars"] > 0 for r in results)
    except Exception as error:                          # noqa: BLE001
        record["loaded"] = record.get("loaded", False)
        record["ok"] = False
        record["error"] = f"{type(error).__name__}: {str(error)[:400]}"
        record["traceback_tail"] = traceback.format_exc()[-1200:]
    finally:
        del llm
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:                               # noqa: BLE001
            pass
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--lengths", default="32768,24576,16384,12288,8192")
    parser.add_argument("--utils", default="0.85,0.90,0.80")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--mm-limit", default='{"image": 0}')
    parser.add_argument("--think-open", default="◁think▷")
    parser.add_argument("--think-close", default="◁/think▷")
    parser.add_argument("--template-kwargs", default="{}")
    parser.add_argument("--reasoning-parser", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    lengths = [int(x) for x in args.lengths.split(",")]
    utils = [float(x) for x in args.utils.split(",")]
    attempts = []
    winner = None
    for max_len in lengths:
        for util in utils:
            print(f"\n=== attempt max_model_len={max_len} util={util}",
                  flush=True)
            record = attempt(
                args.model, args.revision, max_len, util,
                args.trust_remote_code, json.loads(args.mm_limit),
                args.think_open, args.think_close,
                json.loads(args.template_kwargs), args.reasoning_parser)
            attempts.append(record)
            print(f"    loaded={record.get('loaded')} ok={record.get('ok')} "
                  f"{record.get('error', '')[:160]}", flush=True)
            Path(args.out).write_text(json.dumps(
                {"model": args.model, "revision": args.revision,
                 "attempts": attempts,
                 "first_working": winner}, indent=1))
            if record.get("ok"):
                winner = {"max_model_len": max_len,
                          "gpu_memory_utilization": util}
                break
        if winner:
            break

    Path(args.out).write_text(json.dumps(
        {"model": args.model, "revision": args.revision,
         "attempts": attempts, "first_working": winner}, indent=1))
    print(f"\nfirst working envelope: {winner}")
    return 0 if winner else 1


if __name__ == "__main__":
    raise SystemExit(main())
