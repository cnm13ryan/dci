"""Kimi-VL generation backend. Runs in `.venv-kimi`, alone, and imports nothing
from `crossmodel` or `dci`.

Same design-in / rows-out contract as `vllm_tp2.py`, for the same reason: this
file is executed by a DIFFERENT interpreter from the rest of the study. The
checkpoint declares `transformers_version: 4.50.3`; the scientific environment
runs 5.15.0 for the other four checkpoints, and the two cannot share a venv. So
this reads a plan and a design that the scientific environment wrote, generates,
and writes raw rows back. `xm_vllm_ingest.py` then rebuilds the canonical schema
rows, which keeps `crossmodel.schema` the single authority on what a stored row
is and keeps Kimi's rows the same shape as everyone else's.

Four properties this backend must preserve:

**Every weight on a GPU.** A `max_memory` cap even slightly too small does not
fail — accelerate silently pushes the remainder to the meta device and streams
it from disk. That is a different execution condition and unusably slow, so it
is refused, not measured.

**One uninterrupted generation.** Reasoning and answer share one budget and the
model closes its own reasoning. No stop string, no splice, no forced close.

**Per-row scientific seeds.** Each row's seed is a pure function of its
scientific identity, set immediately before its batch is generated.

**No single row can stall the run.** Rows go out in chunks, each chunk is
appended as it completes, and a whole-run deadline writes the remainder as
NOT_GENERATED rather than losing them silently.

    .venv-kimi/bin/python crossmodel/kimi_hf_backend.py \\
        --plan PLAN.json --design DESIGN.jsonl --out raw_generations.jsonl
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import traceback
from pathlib import Path

THINK_OPEN = "◁think▷"
THINK_CLOSE = "◁/think▷"
#: Turn and sequence control tokens, stripped from stored text. `◁think▷` and
#: `◁/think▷` are deliberately NOT here: they are the reasoning boundary and
#: removing them would let the trace flow into the scored answer.
CONTROL_TOKENS = ("<|im_end|>", "<|im_start|>", "<|im_assistant|>",
                  "<|im_user|>", "<|im_system|>", "<|im_middle|>")


def free_vram_gib() -> list[float]:
    try:
        out = subprocess.run(["rocm-smi", "--showmeminfo", "vram", "--json"],
                             capture_output=True, text=True, timeout=60).stdout
        data = json.loads(out)
    except Exception:                                   # noqa: BLE001
        return []
    free = []
    for card in sorted(data):
        try:
            total = float(data[card]["VRAM Total Memory (B)"])
            used = float(data[card]["VRAM Total Used Memory (B)"])
        except (KeyError, TypeError, ValueError):
            continue
        if total / 2 ** 30 < 20.0:
            continue
        free.append(round((total - used) / 2 ** 30, 2))
    return free


def split_reasoning(text: str) -> tuple[str, str]:
    """The model card's own parser, with one deliberate difference.

    Where the card returns the whole text as the summary when no marker is
    present, this returns an EMPTY answer: a scored scratchpad is worse than a
    missing datum. Content emitted BEFORE the opening marker is treated as
    answer, so the split assumes no ordering the template does not enforce.
    """
    if THINK_CLOSE in text:
        head, _, tail = text.partition(THINK_CLOSE)
        if THINK_OPEN in head:
            leading, _, reasoning = head.partition(THINK_OPEN)
        else:
            leading, reasoning = "", head
        answer = f"{leading.strip()}\n{tail.strip()}".strip()
        return reasoning.strip("\n"), answer
    if THINK_OPEN in text:
        return text.split(THINK_OPEN, 1)[1].strip("\n"), ""
    # Markerless output from an ALWAYS-thinking checkpoint means the reasoning
    # interface or the parser failed, so this text is a scratchpad. Returning it
    # as the answer would hand a whole unsegmented generation to the behavioural
    # verifiers and manufacture a datum out of a parser failure. The raw text is
    # preserved by the caller under `raw_generation` for diagnosis; what is
    # refused is its promotion to a final answer.
    return "", ""


def strip_control(text: str) -> str:
    for token in CONTROL_TOKENS:
        text = text.replace(token, "")
    return text.strip()


def trim_generated(tail, tokenizer) -> list[int]:
    """Cut a generated sequence at its real end, before anything decodes it.

    `model.generate` returns a rectangular tensor: in a batch, whichever
    sequence finishes first is RIGHT-padded out to the length of the longest
    one. Slicing the generated span and decoding it with
    `skip_special_tokens=False` therefore appends a run of `[PAD]` to the text —
    and that run reaches the verifiers as answer content, inflates
    `final_answer_tokens`, and makes `answer_truncated` true for a row that
    never came near the ceiling.

    The 24-row pilot caught exactly this: three rows carried 7113–7911 "answer"
    tokens that were almost entirely padding. Trimming here, on token ids, fixes
    all three symptoms at their source rather than papering over the text.

    Everything from the first end-of-sequence token onward is padding or turn
    scaffolding, so the sequence ends there; any trailing pad ids are dropped
    for tokenizers whose eos and pad differ.
    """
    ids = [int(i) for i in tail.tolist()]
    eos = tokenizer.eos_token_id
    if eos is not None and eos in ids:
        ids = ids[:ids.index(eos)]
    pad = tokenizer.pad_token_id
    while ids and pad is not None and ids[-1] == pad:
        ids.pop()
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    plan = json.loads(Path(args.plan).read_text())
    rows = [json.loads(line) for line in Path(args.design).open()]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    import torch
    import transformers

    started = time.perf_counter()
    before = free_vram_gib()

    config = transformers.AutoConfig.from_pretrained(
        plan["model_id"], revision=plan["model_revision"],
        trust_remote_code=True)
    rope_as_loaded = getattr(config.text_config, "rope_scaling", None)

    load_kwargs = dict(
        revision=plan["model_revision"],
        # `torch_dtype`, not `dtype`: this environment is transformers 4.50.3.
        torch_dtype=getattr(torch, plan.get("dtype", "bfloat16")),
        device_map=plan.get("device_map", "auto"),
        attn_implementation="eager", trust_remote_code=True)
    if plan.get("max_memory_per_gpu"):
        load_kwargs["max_memory"] = {i: plan["max_memory_per_gpu"]
                                     for i in range(torch.cuda.device_count())}

    model, info = transformers.AutoModelForCausalLM.from_pretrained(
        plan["model_id"], output_loading_info=True, **load_kwargs)
    missing = list(info.get("missing_keys") or [])
    if missing:
        raise RuntimeError(
            f"{len(missing)} parameter(s) were not found in the checkpoint and "
            f"would have been randomly initialised, e.g. {missing[:3]}. "
            "Generating from partially initialised weights produces noise "
            "indistinguishable from a behavioural failure.")

    placement: dict[str, float] = {}
    for parameter in model.parameters():
        key = str(parameter.device)
        placement[key] = placement.get(key, 0.0) + (
            parameter.numel() * parameter.element_size() / 2 ** 30)
    offloaded = {k: round(v, 2) for k, v in placement.items()
                 if k in ("meta", "cpu", "disk")}
    if offloaded:
        raise RuntimeError(
            f"{offloaded} GiB of weights were placed off-GPU at "
            f"max_memory_per_gpu={plan.get('max_memory_per_gpu')}. Weights "
            "streamed from disk are a different execution condition and are "
            "refused; raise the cap.")

    tokenizer = transformers.AutoTokenizer.from_pretrained(
        plan["model_id"], revision=plan["model_revision"],
        trust_remote_code=True)
    load_seconds = time.perf_counter() - started
    after_load = free_vram_gib()
    print(f"loaded in {load_seconds:.1f}s · weights "
          f"{ {k: round(v, 2) for k, v in sorted(placement.items())} } · free "
          f"{after_load} GiB", flush=True)

    ceiling = int(plan["generation_ceiling"])
    batch_size = int(plan.get("batch_size", 2))
    chunk_size = int(plan.get("chunk_size", 16))
    deadline = plan.get("deadline_seconds")

    pad_marker = tokenizer.pad_token or "[PAD]"

    def record(row, prompt, text, generated_tokens) -> dict:
        cleaned = strip_control(text)
        reasoning, answer = split_reasoning(cleaned)
        if pad_marker and pad_marker in answer:
            # Belt and braces behind trim_generated. A scored answer containing
            # padding is a corrupt datum, not a behavioural one, so it is a
            # technical failure rather than something to clean up and score.
            return failure(row, prompt, ValueError(
                f"{answer.count(pad_marker)} {pad_marker} token(s) survived "
                "into the final answer; padding must never reach a verifier"))
        emitted = bool(reasoning.strip())
        closed = THINK_CLOSE in cleaned
        return {
            "row_id": row["row_id"],
            "rendered_prompt": prompt,
            "raw_generation": text,
            "reasoning_text": reasoning,
            "final_answer": answer,
            "reasoning_tokens": len(tokenizer.encode(
                reasoning, add_special_tokens=False)) if reasoning else 0,
            "final_answer_tokens": len(tokenizer.encode(
                answer, add_special_tokens=False)) if answer else 0,
            "total_generated_tokens": int(generated_tokens),
            "finish_reason": "length" if generated_tokens >= ceiling else "stop",
            "stop_reason": "",
            "reasoning_emitted": emitted,
            "natural_reasoning_closed": closed,
            "reasoning_cap_hit": bool(generated_tokens >= ceiling and not closed),
            "answer_truncated": bool(generated_tokens >= ceiling),
            "seed_reasoning": int(row["scientific_seed"]),
            "not_generated": False,
            "technical_failure": False,
            "technical_failure_reason": "",
        }

    def failure(row, prompt, error) -> dict:
        return {
            "row_id": row["row_id"], "rendered_prompt": prompt,
            "raw_generation": "", "reasoning_text": "", "final_answer": "",
            "reasoning_tokens": 0, "final_answer_tokens": 0,
            "total_generated_tokens": 0, "finish_reason": "error",
            "stop_reason": "", "reasoning_emitted": False,
            "natural_reasoning_closed": False, "reasoning_cap_hit": False,
            "answer_truncated": False,
            "seed_reasoning": int(row["scientific_seed"]),
            "not_generated": False, "technical_failure": True,
            "technical_failure_reason": f"{type(error).__name__}: {error}"[:500]}

    def unattempted(row, why: str) -> dict:
        return {
            "row_id": row["row_id"], "rendered_prompt": "",
            "raw_generation": "", "reasoning_text": "", "final_answer": "",
            "reasoning_tokens": 0, "final_answer_tokens": 0,
            "total_generated_tokens": 0, "finish_reason": "not_generated",
            "stop_reason": "", "reasoning_emitted": False,
            "natural_reasoning_closed": False, "reasoning_cap_hit": False,
            "answer_truncated": False,
            "seed_reasoning": int(row["scientific_seed"]),
            "not_generated": True, "not_generated_reason": why,
            "technical_failure": False, "technical_failure_reason": ""}

    def render(row) -> str:
        messages = ([{"role": "system", "content": row["system_message"]}]
                    if row.get("system_message") else [])
        messages.append({"role": "user", "content": row["user_prompt"]})
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)

    def generate_batch(window: list[dict]) -> list[dict]:
        prompts = [render(row) for row in window]
        encoded = tokenizer(prompts, return_tensors="pt", padding=True,
                            padding_side="left").to(model.device)
        for row in window:
            torch.manual_seed(int(row["scientific_seed"]))
        output = model.generate(
            **encoded, do_sample=True,
            temperature=plan["temperature"], top_p=plan["top_p"],
            top_k=plan["top_k"] or 0, max_new_tokens=ceiling,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
        produced = []
        for row, prompt, sequence in zip(window, prompts, output):
            tail = trim_generated(sequence[encoded["input_ids"].shape[1]:],
                                  tokenizer)
            text = tokenizer.decode(tail, skip_special_tokens=False)
            produced.append(record(row, prompt, text, len(tail)))
        return produced

    records: list[dict] = []
    out.write_text("")
    generation_started = time.perf_counter()
    for start in range(0, len(rows), chunk_size):
        window = rows[start:start + chunk_size]
        spent = time.perf_counter() - generation_started
        if deadline and spent > float(deadline):
            why = (f"whole-run deadline {deadline}s exceeded after {spent:.0f}s "
                   f"and {len(records)} rows")
            chunk = [unattempted(row, why) for row in window]
            print(f"  DEADLINE — {len(window)} rows NOT_GENERATED", flush=True)
        else:
            chunk = []
            for offset in range(0, len(window), batch_size):
                sub = window[offset:offset + batch_size]
                try:
                    chunk += generate_batch(sub)
                except Exception as error:              # noqa: BLE001
                    # A batch that fails is recorded per row, never dropped: a
                    # silently short file is indistinguishable from a design
                    # that never had those cells.
                    print(f"  batch failed — {type(error).__name__}: "
                          f"{str(error)[:160]}", flush=True)
                    traceback.print_exc()
                    chunk += [failure(row, "", error) for row in sub]
        records += chunk
        with out.open("a") as handle:
            for item in chunk:
                handle.write(json.dumps(item) + "\n")
        answered = sum(1 for r in chunk if r["final_answer"].strip())
        print(f"  chunk {start}-{start + len(window)}: {answered}/{len(chunk)} "
              f"answered, {time.perf_counter() - generation_started:.0f}s "
              f"elapsed, free {free_vram_gib()} GiB", flush=True)

    elapsed = time.perf_counter() - started
    engine = {
        "backend": "transformers",
        "backend_version": transformers.__version__,
        "torch_version": torch.__version__,
        "venv": ".venv-kimi",
        "checkpoint_declares_transformers": plan.get(
            "checkpoint_transformers_version"),
        "compatibility_shims_applied": [],
        "rope_scaling_as_loaded": rope_as_loaded,
        "parameter_gib_per_device": {k: round(v, 2)
                                     for k, v in sorted(placement.items())},
        "total_parameter_gib": round(sum(placement.values()), 2),
        "offloaded_gib": offloaded,
        "unexpected_keys": len(info.get("unexpected_keys") or []),
        "load_kwargs": {k: str(v) for k, v in load_kwargs.items()},
        "reasoning_parser": f"delimiters({THINK_OPEN} … {THINK_CLOSE})",
        "chat_template_kwargs": plan.get("chat_template_kwargs", {}),
        "rendered_prompt_example": render(rows[0])[-400:] if rows else "",
        "free_vram_before_load": before,
        "free_vram_after_load": after_load,
        "free_vram_at_end": free_vram_gib(),
        "load_seconds": round(load_seconds, 1),
        "generation_seconds": round(elapsed - load_seconds, 1),
        "rows": len(records),
        "batch_size": batch_size, "chunk_size": chunk_size,
        "generation_ceiling": ceiling, "deadline_seconds": deadline,
    }
    out.with_name(out.stem + "_engine.json").write_text(
        json.dumps(engine, indent=1, default=str))

    caps = sum(1 for r in records if r["reasoning_cap_hit"])
    failures = sum(1 for r in records if r["technical_failure"])
    print(f"\ntransformers {transformers.__version__} · {len(records)} rows "
          f"· batch {batch_size}")
    print(f"  budget {ceiling} tokens/request · cap hits {caps} · "
          f"technical failures {failures} · not generated "
          f"{sum(1 for r in records if r['not_generated'])}")
    print(f"  answers {sum(1 for r in records if r['final_answer'].strip())}"
          f"/{len(records)} · wrote {out}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        raise SystemExit(3)
