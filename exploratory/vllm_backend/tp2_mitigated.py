"""TP=2 with the documented consumer-ROCm mitigations applied.

The previous project's `experiment_utils.py` records that "NCCL collectives
during decode stall indefinitely on tp>1 (observed on 2x RX 7900 XTX)" and works
around it by capping TP at 1. It never tried the two settings that target the
missing peer link directly:

  * `disable_custom_all_reduce=True` — vLLM's custom all-reduce kernel assumes
    peer-to-peer access between cards.
  * `NCCL_P2P_DISABLE=1` — forces RCCL to stage through host memory instead.

This is that attempt, time-boxed. Load is instrumented separately from decode,
because the stall was reported *during decode* and the earlier run did reach the
point of allocating on both cards.
"""
import json
import subprocess
import sys
import time
from dataclasses import replace as _replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vllm_backend import engine as _engine
from vllm_backend.contract import GenerationRequest
from vllm_backend.hardware import probe as _probe_host
from vllm_backend.registry import get_or_default
from vllm_backend.resolve import resolve_engine, resolve_sampling

MODEL = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"


def rocm():
    out = subprocess.run(["rocm-smi", "--showmeminfo", "vram", "--showuse", "--json"],
                         capture_output=True, text=True).stdout
    try:
        data = json.loads(out)
    except Exception:
        return {"raw": out[:200]}
    return {k: (int(v.get("VRAM Total Used Memory (B)", 0)) // 2**20,
                v.get("GPU use (%)"))
            for k, v in data.items() if k != "card2"}


def main():
    print("before:", rocm(), flush=True)
    card = _replace(get_or_default(MODEL), model_id=MODEL)
    plan = resolve_engine(card, _probe_host(), {
        "tensor_parallel_size": 2, "max_model_len": 8192,
        "seed": 20260810, "model_revision": REVISION})
    llm, tok, load_seconds = _engine.build_engine(plan)
    print(f"LOAD_OK in {load_seconds:.1f}s", flush=True)
    print("after load:", rocm(), flush=True)
    cache = llm.llm_engine.vllm_config.cache_config
    print("num_gpu_blocks:", cache.num_gpu_blocks, "block_size:", cache.block_size,
          "=> KV tokens:", (cache.num_gpu_blocks or 0) * cache.block_size, flush=True)

    request = GenerationRequest(
        row_id="smoke",
        user_prompt="In exactly 4 sentences, explain why the sky is blue.")
    prompt = _engine.render_prompt(tok, request, {})
    print("DECODE_START", flush=True)
    started = time.perf_counter()
    outs = llm.generate([prompt], _engine.build_sampling(
        resolve_sampling(max_tokens=128), 128, 1))
    print(f"DECODE_OK {time.perf_counter() - started:.2f}s "
          f"{len(outs[0].outputs[0].token_ids)} tokens", flush=True)
    print("during decode:", rocm(), flush=True)
    print("TEXT:", repr(outs[0].outputs[0].text[:200]), flush=True)


if __name__ == "__main__":
    main()
