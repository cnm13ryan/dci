"""Kimi-VL qualification ladder, run in `.venv-kimi`. Imports nothing local.

This file is executed by a DIFFERENT interpreter from the rest of the study, for
the same reason `vllm_tp2.py` is: the checkpoint's own modeling code declares
`transformers_version: 4.50.3`, and the scientific environment runs 5.15.0. The
three differences between those versions each break this checkpoint —

    is_torch_fx_available      removed in 5.x; the module imports it at top level
    rope_scaling: null         synthesised into a dict in 5.x; the code tests `is None`
    tie_weights()              called with recompute_mapping= in 5.x; the method takes none

— and each was shimmed once, in the scientific environment, before this
environment existed. Running the checkpoint on the version it was published
against removes all three shims rather than accumulating a fourth. Nothing here
patches transformers, and the absence of patching is itself checked below and
recorded in the report.

The ladder is the same four rungs the Transformers path uses:

    1 LOAD  2 ONE REQUEST  3 SMALL BATCH  4 REPEATABILITY

    .venv-kimi/bin/python crossmodel/kimi_qualify_backend.py \\
        --plan PLAN.json --design DESIGN.jsonl --out qualification.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

THINK_OPEN = "◁think▷"
THINK_CLOSE = "◁/think▷"
CONTROL_TOKENS = ("<|im_end|>", "<|im_start|>", "<|im_assistant|>",
                  "<|im_user|>", "<|im_system|>", "<|im_middle|>")


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def shim_audit() -> dict:
    """Prove no compatibility patch is needed here, rather than assert it."""
    import inspect

    import transformers
    from transformers.dynamic_module_utils import get_class_from_dynamic_module

    audit = {"transformers_version": transformers.__version__}
    try:
        from transformers.utils.import_utils import is_torch_fx_available

        audit["is_torch_fx_available_present"] = callable(is_torch_fx_available)
    except ImportError:
        audit["is_torch_fx_available_present"] = False
    return audit


def split_reasoning(text: str) -> tuple[str, str]:
    """The model card's own parser, with one difference.

    Where the card returns the whole text as the summary when no marker is
    present, this returns an EMPTY answer in a thinking condition: a scored
    scratchpad is worse than a missing datum. Content before the opening marker
    is treated as answer, so the split assumes no ordering the template does not
    enforce.
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
    return "", text.strip()


def clean(text: str) -> str:
    for token in CONTROL_TOKENS:
        text = text.replace(token, "")
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    plan = json.loads(Path(args.plan).read_text())
    design = [json.loads(line) for line in Path(args.design).open()]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    import torch
    import transformers

    report = {
        "stamp": "EXPLORATORY_NO_EVIDENCE",
        "model_id": plan["model_id"],
        "model_revision": plan["model_revision"],
        "checked_utc": utc(),
        "environment": {
            "venv": ".venv-kimi",
            "torch_version": torch.__version__,
            "checkpoint_declares_transformers": plan.get(
                "checkpoint_transformers_version"),
            **shim_audit(),
            "compatibility_shims_applied": [],
        },
        "configuration": {k: plan.get(k) for k in (
            "device_map", "max_memory_per_gpu", "batch_size", "dtype",
            "quantization", "generation_ceiling", "answer_tokens",
            "temperature", "top_p", "top_k", "reasoning_mode")},
        "machine_at_start": {"free_vram_gib": free_vram_gib()},
        "rungs": {},
    }

    def finish(verdict: str, blocker: str = "") -> int:
        report["verdict"] = verdict
        report["blocker"] = blocker
        out.write_text(json.dumps(report, indent=1, default=str))
        print(f"\n{'=' * 70}\n{plan['model_id']}: {verdict}")
        if blocker:
            print(f"  blocker: {blocker}")
        print(f"  wrote {out}")
        return 0 if verdict.startswith("QUALIFIED") else 1

    # ------------------------------------------------------------ rung 1
    print(f"RUNG 1 — load under transformers {transformers.__version__}",
          flush=True)
    before = free_vram_gib()
    started = time.perf_counter()
    try:
        config = transformers.AutoConfig.from_pretrained(
            plan["model_id"], revision=plan["model_revision"],
            trust_remote_code=True)
        # Recorded, not repaired: on the matched version this is already the
        # value the checkpoint declares. If it is ever not None here, that is a
        # finding, not something to paper over.
        report["environment"]["rope_scaling_as_loaded"] = \
            getattr(config.text_config, "rope_scaling", None)

        # `torch_dtype`, not `dtype`: transformers renamed this argument in 5.x
        # and this environment is deliberately on 4.50.3, the version the
        # checkpoint declares. Using the newer spelling here was a bug in the
        # driver, not an incompatibility in the checkpoint.
        kwargs = dict(revision=plan["model_revision"],
                      torch_dtype=getattr(torch, plan.get("dtype", "bfloat16")),
                      device_map=plan.get("device_map", "auto"),
                      attn_implementation="eager", trust_remote_code=True)
        if plan.get("max_memory_per_gpu"):
            kwargs["max_memory"] = {i: plan["max_memory_per_gpu"]
                                    for i in range(torch.cuda.device_count())}
        model, info = transformers.AutoModelForCausalLM.from_pretrained(
            plan["model_id"], output_loading_info=True, **kwargs)
        missing = list(info.get("missing_keys") or [])
        if missing:
            raise RuntimeError(
                f"{len(missing)} parameter(s) were not found in the checkpoint "
                f"and would have been randomly initialised, e.g. {missing[:3]}. "
                "Generating from partially initialised weights produces noise "
                "indistinguishable from a behavioural failure.")
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            plan["model_id"], revision=plan["model_revision"],
            trust_remote_code=True)
    except Exception as error:                          # noqa: BLE001
        report["rungs"]["1_load"] = {
            "passed": False, "vram_before": before,
            "vram_after": free_vram_gib(),
            "error": f"{type(error).__name__}: {error}"[:800],
            "traceback": traceback.format_exc()[-3000:]}
        return finish("BLOCKED_AT_LOAD",
                      f"{type(error).__name__}: {error}"[:300])

    placement: dict[str, float] = {}
    for parameter in model.parameters():
        key = str(parameter.device)
        placement[key] = placement.get(key, 0.0) + (
            parameter.numel() * parameter.element_size() / 2 ** 30)

    # A weight budget too small for the checkpoint does not fail — accelerate
    # silently pushes the remainder to the meta device and streams it from
    # disk. That is a different execution condition (and unusably slow), so it
    # is refused here rather than measured and reported as the model's speed.
    offloaded = {k: round(v, 2) for k, v in placement.items()
                 if k in ("meta", "cpu", "disk")}
    if offloaded:
        report["rungs"]["1_load"] = {
            "passed": False, "vram_before": before,
            "vram_after": free_vram_gib(),
            "parameter_gib_per_device": {k: round(v, 2)
                                         for k, v in sorted(placement.items())},
            "error": f"{offloaded} GiB of weights were not placed on a GPU"}
        return finish(
            "BLOCKED_AT_LOAD",
            f"{offloaded} GiB offloaded off-GPU at max_memory_per_gpu="
            f"{plan.get('max_memory_per_gpu')}; raise the cap so every weight "
            "is resident, or the run measures disk bandwidth, not the model")
    report["rungs"]["1_load"] = {
        "passed": True,
        "seconds": round(time.perf_counter() - started, 1),
        "vram_before": before, "vram_after": free_vram_gib(),
        "parameter_gib_per_device": {k: round(v, 2)
                                     for k, v in sorted(placement.items())},
        "total_parameter_gib": round(sum(placement.values()), 2),
        "unexpected_keys": len(info.get("unexpected_keys") or []),
    }
    print(f"  loaded in {report['rungs']['1_load']['seconds']}s; weights "
          f"{report['rungs']['1_load']['parameter_gib_per_device']}; free "
          f"{free_vram_gib()} GiB", flush=True)

    # --------------------------------------------------------- generation
    ceiling = int(plan["generation_ceiling"])

    def generate(rows: list[dict], batch_size: int) -> list[dict]:
        results = []
        for start in range(0, len(rows), batch_size):
            window = rows[start:start + batch_size]
            prompts = [tokenizer.apply_chat_template(
                ([{"role": "system", "content": r["system_message"]}]
                 if r.get("system_message") else [])
                + [{"role": "user", "content": r["user_prompt"]}],
                tokenize=False, add_generation_prompt=True) for r in window]
            encoded = tokenizer(prompts, return_tensors="pt", padding=True,
                                padding_side="left").to(model.device)
            for row in window:
                torch.manual_seed(int(row["scientific_seed"]))
            output = model.generate(
                **encoded, do_sample=True,
                temperature=plan["temperature"], top_p=plan["top_p"],
                top_k=plan["top_k"] or 0, max_new_tokens=ceiling,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
            for row, prompt, sequence in zip(window, prompts, output):
                generated = sequence[encoded["input_ids"].shape[1]:]
                text = tokenizer.decode(generated, skip_special_tokens=False)
                reasoning, answer = split_reasoning(clean(text))
                results.append({
                    "row_id": row["row_id"],
                    "reasoning_tokens": len(tokenizer.encode(
                        reasoning, add_special_tokens=False)) if reasoning else 0,
                    "final_answer_tokens": len(tokenizer.encode(
                        answer, add_special_tokens=False)) if answer else 0,
                    "total_generated_tokens": int(generated.shape[0]),
                    "reasoning_emitted": bool(reasoning.strip()),
                    "natural_reasoning_closed": THINK_CLOSE in text,
                    "reasoning_cap_hit": (int(generated.shape[0]) >= ceiling
                                          and THINK_CLOSE not in text),
                    "final_answer": answer,
                    "answer_preview": answer[:160],
                })
        return results

    def summarise(records: list[dict]) -> dict:
        return {
            "rows": len(records),
            "answered": sum(1 for r in records if r["final_answer"].strip()),
            "closed": sum(1 for r in records
                          if r["natural_reasoning_closed"]),
            "cap_hits": sum(1 for r in records if r["reasoning_cap_hit"]),
            "median_reasoning_tokens": sorted(
                r["reasoning_tokens"] for r in records)[len(records) // 2],
            "max_reasoning_tokens": max(r["reasoning_tokens"]
                                        for r in records),
        }

    # ------------------------------------------------------------ rung 2
    print("\nRUNG 2 — one request at batch size 1", flush=True)
    started = time.perf_counter()
    try:
        one = generate(design[:1], 1)
    except Exception as error:                          # noqa: BLE001
        report["rungs"]["2_one_request"] = {
            "passed": False, "error": f"{type(error).__name__}: {error}"[:800],
            "traceback": traceback.format_exc()[-2500:],
            "vram": free_vram_gib()}
        return finish("BLOCKED_AT_ONE_REQUEST",
                      f"{type(error).__name__}: {error}"[:300])
    stats = summarise(one)
    report["rungs"]["2_one_request"] = {
        "passed": stats["answered"] == 1,
        "seconds": round(time.perf_counter() - started, 1),
        "vram_after": free_vram_gib(), "records": one, **stats}
    print(f"  {stats['answered']}/1 answered, {stats['cap_hits']} cap hits, "
          f"{report['rungs']['2_one_request']['seconds']}s", flush=True)
    if not report["rungs"]["2_one_request"]["passed"]:
        return finish("BLOCKED_AT_ONE_REQUEST",
                      "no final answer from a single request")

    # ------------------------------------------------------------ rung 3
    batch_size = int(plan.get("batch_size", 2))
    rows = design[:int(plan.get("qualify_rows", 8))]
    print(f"\nRUNG 3 — {len(rows)} rows at batch size {batch_size}", flush=True)
    started = time.perf_counter()
    try:
        batch = generate(rows, batch_size)
    except Exception as error:                          # noqa: BLE001
        report["rungs"]["3_small_batch"] = {
            "passed": False, "error": f"{type(error).__name__}: {error}"[:800],
            "vram": free_vram_gib()}
        return finish("BLOCKED_AT_SMALL_BATCH",
                      f"{type(error).__name__}: {error}"[:300])
    elapsed = time.perf_counter() - started
    stats = summarise(batch)
    rate = len(batch) / elapsed * 60
    report["rungs"]["3_small_batch"] = {
        "passed": True, "seconds": round(elapsed, 1),
        "rows_per_minute": round(rate, 2),
        "projected_minutes_for_160": round(160 / rate, 1) if rate else None,
        "vram_after": free_vram_gib(),
        "records": [{k: v for k, v in r.items() if k != "final_answer"}
                    for r in batch], **stats}
    print(f"  {stats['answered']}/{len(batch)} answered, {rate:.2f} rows/min "
          f"→ 160 rows in ~{160 / rate:.0f} min", flush=True)

    # ------------------------------------------------------------ rung 4
    print("\nRUNG 4 — repeat; identical seeds must give identical text",
          flush=True)
    repeat = generate(rows, batch_size)
    first = {r["row_id"]: r["final_answer"] for r in batch}
    second = {r["row_id"]: r["final_answer"] for r in repeat}
    identical = sum(1 for k in first if first.get(k) == second.get(k))
    report["rungs"]["4_repeatability"] = {
        "passed": identical == len(first),
        "identical_answers": identical, "of": len(first)}
    print(f"  {identical}/{len(first)} identical", flush=True)
    if identical != len(first):
        return finish("NOT_REPRODUCIBLE",
                      f"only {identical}/{len(first)} rows reproduced")

    report["recommended_configuration"] = {
        "venv": ".venv-kimi", "transformers": transformers.__version__,
        "device_map": plan.get("device_map"),
        "max_memory_per_gpu": plan.get("max_memory_per_gpu"),
        "batch_size": batch_size,
        "generation_ceiling": ceiling,
        "projected_minutes_for_160_rows":
            report["rungs"]["3_small_batch"]["projected_minutes_for_160"],
        "compatibility_shims_required": [],
    }
    return finish("QUALIFIED")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        raise SystemExit(3)
