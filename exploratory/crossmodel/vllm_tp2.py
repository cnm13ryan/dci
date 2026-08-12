"""vLLM tensor-parallel-2 generation backend. Runs in `.venv-vllm`, alone.

This module is executed by a DIFFERENT interpreter from the rest of the study.
vLLM 0.27.1+rocm723 requires torch 2.11, and the scientific environment pins
torch 2.9.1; the two cannot share a virtualenv. That is not a workaround, it is
the repository's existing pattern — `vllm_backend/natural_reasoning.py` already
says "generation happened in the ROCm vLLM environment; scoring happens here".

So this file imports **nothing** from `crossmodel` or `dci`. It reads a plan and
a design that the scientific environment wrote, generates, and writes raw rows
back. `xm_vllm_ingest.py` then rebuilds the canonical schema rows in the
scientific environment, so `crossmodel.schema` stays the single authority on
what a stored row is.

Three properties this backend must preserve, each of which the previous
Transformers attempt had to fight for:

**One uninterrupted generation.** No stop string, no splice, no forced close.
The earlier two-phase splice produced a documented artefact — the model kept
thinking into the answer phase, emitted a second close marker, and re-answered.
Thinking is bounded by a token ceiling, never interrupted mid-stream: a request
that reaches the ceiling stops there and is recorded as NO_FINAL_WITHIN_BUDGET.
Nothing here closes a trace on the model's behalf or invents an answer.

**No single row can stall the run.** Requests are issued in chunks and each
chunk is appended to the output as it completes, so a stopped run still leaves
every finished row on disk. A whole-run wall-clock deadline is a backstop: rows
past it are written as NOT_GENERATED, which is a missing datum, not a failure
and not a behavioural result.

**Per-request scientific seeds.** vLLM's scheduler batches and reorders freely.
Each request therefore carries its own `SamplingParams.seed`, taken from the
design row's `scientific_seed`, which is a pure function of scientific identity.
Nothing about batch position, scheduler order or GPU rank can reach it.

**Model-aware reasoning extraction.** Where vLLM registers a reasoning parser
for the family (`qwen3`, `gemma4`), that parser splits the output. Where it does
not — Kimi-VL — the checkpoint's own documented delimiters are used. Raw text is
never scored.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import traceback
from pathlib import Path


def gpu_memory() -> dict:
    """Resident VRAM per visible device, for the capacity record."""
    try:
        import torch

        if not torch.cuda.is_available():
            return {}
        return {f"cuda:{i}": round(torch.cuda.memory_allocated(i) / 2 ** 30, 3)
                for i in range(torch.cuda.device_count())}
    except Exception:                                   # noqa: BLE001
        return {}


def rocm_smi_memory() -> dict:
    """Per-GPU VRAM from rocm-smi — the only view that sees ALL TP workers.

    `torch.cuda.memory_allocated` reports the calling process only. Under
    tensor parallelism vLLM runs one worker process per rank, so the driver's
    own accounting is what shows whether rank 1 actually holds weights. "Is the
    12B really sharded, or is GPU 1 idle?" cannot be answered any other way.
    """
    import re
    import subprocess

    try:
        out = subprocess.run(["rocm-smi", "--showmemuse", "--json"],
                             capture_output=True, text=True, timeout=60).stdout
        return json.loads(out)
    except Exception:                                   # noqa: BLE001
        try:
            out = subprocess.run(["rocm-smi", "--showmemuse"],
                                 capture_output=True, text=True,
                                 timeout=60).stdout
            found = re.findall(r"GPU\[(\d+)\].*?(\d+)\s*$", out, re.M)
            return {f"GPU[{i}]": v for i, v in found}
        except Exception:                               # noqa: BLE001
            return {}


# ------------------------------------------------------------------ parsing
class DelimiterParser:
    """Fallback splitter for a checkpoint vLLM registers no parser for.

    Used only for Kimi-VL-A3B-Thinking-2506, whose model card ships the
    reference implementation:

        extract_thinking_and_summary(text, bot="◁think▷", eot="◁/think▷")

    with one deliberate difference. Where the card returns the whole text as the
    summary when no marker is present, this returns an EMPTY answer in a
    thinking condition, because a scored scratchpad is worse than a missing
    datum. Content emitted BEFORE the opening marker is treated as answer, so
    the split does not assume an ordering the template does not enforce.
    """

    def __init__(self, start: str, end: str):
        self.start, self.end = start, end

    def extract_reasoning(self, text: str, request=None):
        if self.end in text:
            head, _, tail = text.partition(self.end)
            if self.start in head:
                leading, _, reasoning = head.partition(self.start)
            else:
                leading, reasoning = "", head
            answer = f"{leading.strip()}\n{tail.strip()}".strip()
            return reasoning.strip("\n"), answer
        if self.start in text:
            return text.split(self.start, 1)[1].strip("\n"), ""
        return None, text.strip()


def build_parser(name: str | None, tokenizer, start: str, end: str):
    """vLLM's registered parser when there is one, the delimiters otherwise."""
    if not name:
        return DelimiterParser(start, end), f"delimiters({start} … {end})"
    from vllm.reasoning import ReasoningParserManager

    cls = ReasoningParserManager.get_reasoning_parser(name)
    return cls(tokenizer), f"vllm:{name}"


def split(parser, text: str) -> tuple[str, str]:
    """`(reasoning, answer)`, never raising, never returning raw text as both."""
    try:
        reasoning, content = parser.extract_reasoning(text, None)
    except Exception:                                   # noqa: BLE001
        try:
            reasoning, content = parser.extract_reasoning(text)
        except Exception:                               # noqa: BLE001
            return "", ""
    return (reasoning or "").strip("\n"), (content or "").strip()


# --------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--chunk-size", type=int, default=None,
                        help="requests per llm.generate call; each chunk is "
                             "appended as it finishes")
    parser.add_argument("--deadline-seconds", type=float, default=None,
                        help="whole-run wall-clock backstop; rows past it are "
                             "written NOT_GENERATED")
    args = parser.parse_args()

    plan = json.loads(Path(args.plan).read_text())
    rows = [json.loads(line) for line in Path(args.design).open()]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    from vllm import LLM, SamplingParams
    import vllm

    engine_kwargs = dict(
        model=plan["model_id"],
        revision=plan["model_revision"],
        dtype=plan["dtype"],
        tensor_parallel_size=plan["tensor_parallel_size"],
        max_model_len=plan["max_model_len"],
        gpu_memory_utilization=plan.get("gpu_memory_utilization", 0.85),
        # The ROCm mitigation carried over from the machine's known-working
        # TP=2 runs. The flag still exists in 0.27.1 (vllm/config/parallel.py).
        disable_custom_all_reduce=plan.get("disable_custom_all_reduce", True),
        seed=plan.get("engine_seed", 20260812),
        enforce_eager=plan.get("enforce_eager", True),
        trust_remote_code=plan.get("trust_remote_code", False),
    )
    if plan.get("cpu_offload_gb"):
        # vLLM's own weight-offload knob: per GPU, weights above this stay in
        # pinned host memory and stream in. BF16 throughout — this trades
        # bandwidth for VRAM, it does not change the numbers the model holds.
        engine_kwargs["cpu_offload_gb"] = float(plan["cpu_offload_gb"])
    if plan.get("limit_mm_per_prompt"):
        # Officially supported text-only knob for a multimodal checkpoint: it
        # stops vLLM reserving multimodal cache the DCI prompts never use.
        engine_kwargs["limit_mm_per_prompt"] = plan["limit_mm_per_prompt"]

    before = rocm_smi_memory()
    started = time.perf_counter()
    llm = LLM(**engine_kwargs)
    load_seconds = time.perf_counter() - started
    after = rocm_smi_memory()

    tokenizer = llm.get_tokenizer()
    reasoning_parser, parser_label = build_parser(
        plan.get("reasoning_parser"), tokenizer,
        plan.get("think_open", "<think>"), plan.get("think_close", "</think>"))

    template_kwargs = plan.get("chat_template_kwargs") or {}
    prompts, seeds = [], []
    for row in rows:
        messages = []
        if row.get("system_message"):
            messages.append({"role": "system",
                             "content": row["system_message"]})
        messages.append({"role": "user", "content": row["user_prompt"]})
        prompts.append(tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            **template_kwargs))
        seeds.append(int(row["scientific_seed"]))

    ceiling = int(plan["engineering_ceiling"])
    answer_allowance = int(plan["answer_tokens"])
    # The bounded condition names ONE number: the total tokens a request may
    # produce, reasoning and answer together. `generation_ceiling` states it
    # directly; older plans state it as reasoning ceiling + answer allowance.
    budget = int(plan.get("generation_ceiling") or ceiling + answer_allowance)
    sampling = [SamplingParams(
        temperature=plan["temperature"], top_p=plan["top_p"],
        # top_k <= 0 disables it in vLLM, matching the canonical run which
        # left it unset. Transformers defaults it to 50; vLLM does not.
        top_k=plan.get("top_k", 0) or -1,
        # ONE uninterrupted generation: reasoning and answer share the budget
        # and the model closes its own reasoning. No stop string.
        max_tokens=budget,
        seed=seed) for seed in seeds]

    def build_record(row, prompt, request_output, seed) -> dict:
        try:
            completion = request_output.outputs[0]
            text = completion.text
            reasoning, answer = split(reasoning_parser, text)
            emitted = bool(reasoning.strip())
            closed = emitted and bool(answer.strip() or
                                      plan.get("think_close", "") in text)
            n_tokens = len(completion.token_ids)
            reasoning_tokens = (
                len(tokenizer.encode(reasoning, add_special_tokens=False))
                if reasoning else 0)
            answer_tokens = (
                len(tokenizer.encode(answer, add_special_tokens=False))
                if answer else 0)
            return {
                "row_id": row["row_id"],
                "rendered_prompt": prompt,
                "raw_generation": text,
                "reasoning_text": reasoning,
                "final_answer": answer,
                "reasoning_tokens": reasoning_tokens,
                "final_answer_tokens": answer_tokens,
                "total_generated_tokens": n_tokens,
                "finish_reason": completion.finish_reason,
                "stop_reason": str(completion.stop_reason),
                "reasoning_emitted": emitted,
                "natural_reasoning_closed": closed,
                # The ceiling binds only when the whole budget was consumed
                # without the model ever closing its reasoning.
                "reasoning_cap_hit": (completion.finish_reason == "length"
                                      and not closed),
                "answer_truncated": completion.finish_reason == "length",
                "seed_reasoning": seed,
                "not_generated": False,
                "technical_failure": False,
                "technical_failure_reason": "",
            }
        except Exception as error:                      # noqa: BLE001
            return {
                "row_id": row["row_id"], "rendered_prompt": prompt,
                "raw_generation": "", "reasoning_text": "", "final_answer": "",
                "reasoning_tokens": 0, "final_answer_tokens": 0,
                "total_generated_tokens": 0, "finish_reason": "error",
                "stop_reason": "", "reasoning_emitted": False,
                "natural_reasoning_closed": False, "reasoning_cap_hit": False,
                "answer_truncated": False, "seed_reasoning": seed,
                "not_generated": False,
                "technical_failure": True,
                "technical_failure_reason":
                    f"{type(error).__name__}: {error}"[:500]}

    def unattempted(row, prompt, seed, why: str) -> dict:
        """A row the run never asked for. Missing, not failed, not zero."""
        return {
            "row_id": row["row_id"], "rendered_prompt": prompt,
            "raw_generation": "", "reasoning_text": "", "final_answer": "",
            "reasoning_tokens": 0, "final_answer_tokens": 0,
            "total_generated_tokens": 0, "finish_reason": "not_generated",
            "stop_reason": "", "reasoning_emitted": False,
            "natural_reasoning_closed": False, "reasoning_cap_hit": False,
            "answer_truncated": False, "seed_reasoning": seed,
            "not_generated": True, "not_generated_reason": why,
            "technical_failure": False, "technical_failure_reason": ""}

    chunk_size = int(args.chunk_size or plan.get("chunk_size") or len(rows))
    deadline = args.deadline_seconds or plan.get("deadline_seconds")
    generation_started = time.perf_counter()

    records = []
    out.write_text("")                       # a resumed run starts clean
    for start in range(0, len(rows), chunk_size):
        stop_at = min(start + chunk_size, len(rows))
        window = slice(start, stop_at)
        spent = time.perf_counter() - generation_started
        if deadline and spent > float(deadline):
            why = (f"whole-run deadline {deadline}s exceeded after "
                   f"{spent:.0f}s and {len(records)} rows")
            chunk = [unattempted(r, p, s, why) for r, p, s
                     in zip(rows[window], prompts[window], seeds[window])]
            print(f"  DEADLINE — {stop_at - start} rows NOT_GENERATED",
                  flush=True)
        else:
            generated = llm.generate(prompts[window], sampling[window])
            chunk = [build_record(r, p, g, s) for r, p, g, s
                     in zip(rows[window], prompts[window], generated,
                            seeds[window])]
        records += chunk
        # Appended per chunk so a run stopped by hand, by the deadline or by
        # the machine still leaves every completed row on disk.
        with out.open("a") as handle:
            for record in chunk:
                handle.write(json.dumps(record) + "\n")
        answered = sum(1 for r in chunk if r["final_answer"].strip())
        print(f"  chunk {start}-{stop_at}: {answered}/{len(chunk)} answered, "
              f"{time.perf_counter() - generation_started:.0f}s elapsed",
              flush=True)
    elapsed = time.perf_counter() - started

    engine = {
        "vllm_version": vllm.__version__,
        "vllm_build": os.environ.get("VLLM_BUILD_SHA", ""),
        "engine_kwargs": {k: str(v) for k, v in engine_kwargs.items()},
        "reasoning_parser": parser_label,
        "chat_template_kwargs": template_kwargs,
        "generation_ceiling": budget,
        "chunk_size": chunk_size,
        "deadline_seconds": deadline,
        "rows_not_generated": sum(1 for r in records if r["not_generated"]),
        "rendered_prompt_example": prompts[0][-400:] if prompts else "",
        "load_seconds": round(load_seconds, 1),
        "generation_seconds": round(elapsed - load_seconds, 1),
        "rows": len(records),
        "rocm_smi_before_load": before,
        "rocm_smi_after_load": after,
        "torch_memory_this_process": gpu_memory(),
        "env": {k: v for k, v in os.environ.items()
                if k.startswith(("NCCL_", "RCCL_", "HIP_", "VLLM_", "ROCR_",
                                 "PYTORCH_"))},
    }
    out.with_name(out.stem + "_engine.json").write_text(
        json.dumps(engine, indent=1, default=str))

    caps = sum(1 for r in records if r["reasoning_cap_hit"])
    print(f"\nvLLM TP={plan['tensor_parallel_size']} · {len(records)} rows "
          f"· parser {parser_label}")
    print(f"  budget {budget} tokens/request · cap hits {caps} · not generated "
          f"{sum(1 for r in records if r['not_generated'])}")
    print(f"  reasoning emitted "
          f"{sum(1 for r in records if r['reasoning_emitted'])}/{len(records)}"
          f" · empty answers "
          f"{sum(1 for r in records if not r['final_answer'].strip())}")
    print(f"  wrote {out}")
    return 1 if caps else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        raise SystemExit(3)
