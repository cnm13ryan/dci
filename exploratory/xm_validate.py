"""Stages A, B and C: environment, loading, and the reasoning interface.

Nothing scientific runs here. The question this script answers is the one the
final operating principle insists comes first:

    did we execute this model in a way that preserves the same treatment?

It writes a machine-readable record per checkpoint and classifies each as
LOAD_VALID / LOAD_BLOCKED / BACKEND_BLOCKED / NUMERICAL_CONDITION_BLOCKED, plus a
per-mode reasoning-interface verdict. Every smoke output is saved in full so the
manual inspection the reasoning gate depends on has something to inspect.

    uv run python xm_validate.py --models Qwen/Qwen3.5-4B [--out runs/DIR]
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract
from crossmodel.adapters import CHECKPOINTS, get_adapter
from crossmodel.adapters.base import GenerationConfig
from crossmodel.contract import ReasoningMode

#: Prompts for the reasoning-interface smoke, with a substring any competent
#: checkpoint must produce. Deliberately NOT the DCI tasks: the competence gate
#: uses disjoint material, and a reasoning interface should be validated on
#: prompts whose answers are obvious to a human reader.
#:
#: The expected substrings are a WEIGHT-INTEGRITY check, not an ability test.
#: `Gemma4ForCausalLM` against a conditional-generation checkpoint loads without
#: raising, leaves every parameter randomly initialised, and emits fluent-looking
#: multilingual noise. Nothing downstream would have noticed: the noise simply
#: fails "write exactly 4 sentences" and reads as a behavioural result. A model
#: that cannot name the capital of Japan has not loaded.
#: The last two carry composed constraints on purpose. Gemma 4's template leaves
#: thinking optional and the model DECLINES to open a thought channel on trivial
#: questions — a property of the checkpoint, not a broken parser. A smoke set of
#: only trivial questions cannot tell those two apart, so it cannot validate a
#: reasoning interface. These are still disjoint from the DCI task bank.
SMOKE_PROMPTS = [
    ("Name the capital city of Japan.", "tokyo"),
    ("What is 17 plus 25?", "42"),
    ("Write exactly three sentences about bicycles, each one longer than "
     "the last, and use exactly one comma in the whole answer.", None),
    ("List the first three prime numbers, then explain in exactly two "
     "sentences why the first of them is prime.", "5"),
]

#: A reasoning ceiling for the smoke only. The scientific ceiling is derived per
#: checkpoint from its own context envelope at Stage E.
SMOKE_REASONING_CEILING = 8192

#: Chat-control markup of the shapes the tested families use. Matching on the
#: SHAPE rather than on a list of known tokens is what makes this a check on the
#: cleaning code instead of a restatement of it.
CONTROL_RESIDUE = re.compile(r"<\|[^>]{0,40}\|?>|<[^<>]{0,40}\|>|◁/?[a-z]+▷")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ------------------------------------------------------------------ Stage A
def stage_a_environment() -> dict:
    """The machine, recorded before anything is loaded onto it."""
    import torch
    import transformers

    def run(command: list[str]) -> str:
        try:
            return subprocess.run(command, capture_output=True, text=True,
                                  timeout=60).stdout.strip()
        except Exception as error:                      # noqa: BLE001
            return f"<{type(error).__name__}: {error}>"

    devices = []
    for index in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(index)
        devices.append({
            "index": index, "name": props.name,
            "gcn_arch": getattr(props, "gcnArchName", None),
            "total_memory_gib": round(props.total_memory / 2 ** 30, 2),
            "multi_processor_count": props.multi_processor_count})

    try:
        import vllm
        vllm_version = vllm.__version__
    except Exception:                                   # noqa: BLE001
        vllm_version = None

    environment = {
        "stamp": "EXPLORATORY_NO_EVIDENCE",
        "recorded_utc": utc_stamp(),
        "host": platform.node(),
        "kernel": platform.release(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch_version": torch.__version__,
        "torch_hip_version": torch.version.hip,
        "torch_cuda_version": torch.version.cuda,
        "is_rocm_build": torch.version.hip is not None,
        "transformers_version": transformers.__version__,
        "vllm_version": vllm_version,
        "vllm_available": vllm_version is not None,
        "torch_cuda_is_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
        "devices": devices,
        "bf16_supported": torch.cuda.is_bf16_supported(),
        "rocm_version": Path("/opt/rocm/.info/version").read_text().strip()
                        if Path("/opt/rocm/.info/version").exists() else None,
        "rocm_smi": run(["rocm-smi", "--showproductname"]),
        "disk_free": run(["df", "-h", str(Path.home())]),
        "hf_cache": str(Path.home() / ".cache" / "huggingface" / "hub"),
        "git_commit": run(["git", "rev-parse", "HEAD"]),
        "git_branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "git_dirty": bool(run(["git", "status", "--porcelain"])),
    }

    # A GPU that reports itself is not a GPU that computes. Exercise both.
    smoke = []
    for index in range(torch.cuda.device_count()):
        try:
            started = time.perf_counter()
            a = torch.randn(2048, 2048, device=f"cuda:{index}",
                            dtype=torch.bfloat16)
            product = (a @ a).float()
            torch.cuda.synchronize(index)
            smoke.append({"device": index, "ok": bool(product.isfinite().all()),
                          "seconds": round(time.perf_counter() - started, 3),
                          "dtype": "bfloat16"})
            del a, product
            torch.cuda.empty_cache()
        except Exception as error:                      # noqa: BLE001
            smoke.append({"device": index, "ok": False,
                          "error": f"{type(error).__name__}: {error}"})
    environment["gpu_bf16_matmul_smoke"] = smoke
    environment["environment_ok"] = (
        environment["torch_cuda_is_available"]
        and environment["bf16_supported"]
        and environment["device_count"] >= 1
        and all(s.get("ok") for s in smoke))
    return environment


# ------------------------------------------------------------- Stages B & C
def stage_bc_checkpoint(model_id: str, device_map, out_dir: Path) -> dict:
    """Resolve, load, generate, parse, unload — and say what happened."""
    import torch

    record: dict = {"model_id": model_id, "device_map": str(device_map),
                    "checked_utc": utc_stamp()}
    adapter = get_adapter(model_id, device_map=device_map)
    record["adapter_class"] = type(adapter).__name__
    record["family"] = adapter.FAMILY
    record["supported_modes"] = list(adapter.SUPPORTED_MODES)

    # -- revision -----------------------------------------------------------
    try:
        record["model_revision"] = adapter.resolve_revision()
    except Exception as error:                          # noqa: BLE001
        record["load_status"] = "LOAD_BLOCKED"
        record["blocked_reason"] = f"revision: {error}"
        return record

    # -- load ---------------------------------------------------------------
    try:
        started = time.perf_counter()
        adapter.load()
        record["load_seconds"] = round(time.perf_counter() - started, 1)
        record["load_status"] = "LOAD_VALID"
    except Exception as error:                          # noqa: BLE001
        text = f"{type(error).__name__}: {error}"
        record["load_status"] = _classify_load_failure(text)
        record["blocked_reason"] = text[:1200]
        record["traceback"] = traceback.format_exc()[-2500:]
        return record

    record["execution_metadata"] = _jsonable(adapter.execution_metadata())
    record["peak_memory_after_load_gib"] = {
        f"cuda:{i}": round(torch.cuda.max_memory_allocated(i) / 2 ** 30, 3)
        for i in range(torch.cuda.device_count())}

    # -- Stage C: one verdict per supported reasoning mode -------------------
    system = _system_message()
    record["modes"] = {}
    for mode in adapter.SUPPORTED_MODES:
        record["modes"][mode] = _probe_mode(adapter, mode, system, out_dir)

    try:
        adapter.unload()
        record["unloaded"] = True
        record["memory_after_unload_gib"] = {
            f"cuda:{i}": round(torch.cuda.memory_allocated(i) / 2 ** 30, 3)
            for i in range(torch.cuda.device_count())}
    except Exception as error:                          # noqa: BLE001
        record["unloaded"] = False
        record["unload_error"] = f"{type(error).__name__}: {error}"
    return record


def _probe_mode(adapter, mode: str, system: str, out_dir: Path) -> dict:
    """Generate the smoke set in one mode and check the channel separation."""
    verdict: dict = {"reasoning_mode": mode}
    texts = [text for text, _ in SMOKE_PROMPTS]
    expected = [want for _, want in SMOKE_PROMPTS]
    try:
        prompts = [adapter.render_prompt(
            [{"role": "system", "content": system},
             {"role": "user", "content": text}], mode)
            for text in texts]
        verdict["rendered_prompt_tail"] = prompts[0][-300:]

        config = GenerationConfig(
            reasoning_mode=mode, max_answer_tokens=contract.ANSWER_TOKENS,
            temperature=contract.TEMPERATURE, top_p=contract.TOP_P,
            top_k=contract.TOP_K,
            max_reasoning_tokens=(0 if mode == ReasoningMode.NO_THINKING
                                  else SMOKE_REASONING_CEILING))
        seeds = [(1000 + i, 2000 + i) for i in range(len(prompts))]
        started = time.perf_counter()
        generations = adapter.generate(prompts, seeds, config)
        verdict["seconds"] = round(time.perf_counter() - started, 1)
    except Exception as error:                          # noqa: BLE001
        verdict["status"] = "MODE_FAILED"
        verdict["error"] = f"{type(error).__name__}: {error}"
        verdict["traceback"] = traceback.format_exc()[-2000:]
        return verdict

    # Save every smoke output in full: the reasoning gate passes only after a
    # human has read these, and a truncated sample cannot be read.
    path = out_dir / f"smoke_{adapter.MODEL_ID.replace('/', '_')}_{mode}.jsonl"
    with path.open("w") as handle:
        for prompt_text, generation in zip(texts, generations):
            handle.write(json.dumps({
                "smoke_prompt": prompt_text,
                "rendered_prompt": generation.prompt,
                "raw_generation": generation.raw_generation,
                "reasoning_text": generation.reasoning_text,
                "final_answer": generation.final_answer,
                "reasoning_tokens": generation.reasoning_tokens,
                "final_answer_tokens": generation.final_answer_tokens,
                "natural_reasoning_closed": generation.natural_reasoning_closed,
                "reasoning_cap_hit": generation.reasoning_cap_hit,
                "answer_truncated": generation.answer_truncated,
                "finish_reason": generation.finish_reason}) + "\n")
    verdict["smoke_file"] = str(path)

    markers = [adapter.THINK_OPEN, adapter.THINK_CLOSE]
    answers = [g.final_answer for g in generations]
    verdict.update({
        "n": len(generations),
        "answers_non_empty": sum(1 for a in answers if a.strip()),
        "marker_leak_into_answer": sum(
            1 for a in answers if any(m in a for m in markers)),
        # Any chat-control markup surviving into the answer would be handed to a
        # sentence-count verifier as if it were prose. The first Qwen smoke run
        # ended every answer with `<|im_end|>`; this is what caught it.
        "control_token_residue": sum(
            1 for a in answers if CONTROL_RESIDUE.search(a)),
        "residue_examples": [CONTROL_RESIDUE.findall(a)[:3]
                             for a in answers if CONTROL_RESIDUE.search(a)][:3],
        "reasoning_present": sum(1 for g in generations
                                 if g.reasoning_text.strip()),
        "reasoning_emitted": sum(1 for g in generations if g.reasoning_emitted),
        "closed_naturally": sum(1 for g in generations
                                if g.natural_reasoning_closed),
        "cap_hits": sum(1 for g in generations if g.reasoning_cap_hit),
        "answers_truncated": sum(1 for g in generations if g.answer_truncated),
        "median_reasoning_tokens": sorted(
            g.reasoning_tokens for g in generations)[len(generations) // 2],
        "example_answer": answers[0][:400],
        "example_reasoning": generations[0].reasoning_text[:400],
        "weight_integrity_checks": sum(1 for w in expected if w),
        "weight_integrity_passed": sum(
            1 for answer, want in zip(answers, expected)
            if want and want in answer.lower()),
    })

    problems = []
    if verdict["answers_non_empty"] != verdict["n"]:
        problems.append("empty final answer")
    if verdict["marker_leak_into_answer"]:
        problems.append("reasoning marker inside the final answer")
    if verdict["control_token_residue"]:
        problems.append("chat-control markup inside the final answer")
    if verdict["weight_integrity_passed"] == 0:
        problems.append(
            "WEIGHTS SUSPECT — not one trivial question was answered "
            "correctly, which is what a partially initialised load looks like")
    if mode == ReasoningMode.NO_THINKING:
        # The native control must genuinely answer without a trace.
        if verdict["reasoning_present"]:
            problems.append("a reasoning trace appeared in the non-thinking mode")
    else:
        # Opening a block and failing to close it is a parser/ceiling problem.
        # Never opening one is a choice the checkpoint made, and is reported
        # rather than treated as a defect.
        unclosed = verdict["reasoning_emitted"] - verdict["closed_naturally"]
        if unclosed:
            problems.append(f"{unclosed} trace(s) opened but never closed")
        if verdict["reasoning_emitted"] == 0:
            problems.append("the thinking mode never opened a reasoning block")
        elif verdict["reasoning_emitted"] < verdict["n"]:
            verdict["notes"] = (
                f"{verdict['n'] - verdict['reasoning_emitted']} of "
                f"{verdict['n']} prompts were answered without opening a "
                "reasoning block — the checkpoint chose not to think")
    verdict["problems"] = problems
    verdict["status"] = "MODE_VALID" if not problems else "MODE_SUSPECT"
    return verdict


def _classify_load_failure(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ("out of memory", "hip out of memory",
                                  "cuda out of memory")):
        return "NUMERICAL_CONDITION_BLOCKED"
    if any(k in lowered for k in ("does not recognize", "unrecognized",
                                  "trust_remote_code", "no module named",
                                  "cannot import", "attributeerror",
                                  "importerror", "typeerror")):
        return "BACKEND_BLOCKED"
    return "LOAD_BLOCKED"


def _system_message() -> str:
    from dci_exploratory import extensions, harvest

    extensions.register()
    return harvest.load().SYSTEM_MESSAGE


def _jsonable(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return {k: str(v) for k, v in value.items()}


# ---------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="*", default=list(CHECKPOINTS))
    parser.add_argument("--device-map", default="cuda:0",
                        help="'cuda:0', 'cuda:1', 'auto' (both cards), or "
                             "'balanced'")
    parser.add_argument("--out", default=None)
    parser.add_argument("--skip-environment", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out or f"runs/xm_validate_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"writing to {out_dir}\n")

    if not args.skip_environment:
        environment = stage_a_environment()
        (out_dir / "environment.json").write_text(
            json.dumps(environment, indent=1))
        print("STAGE A — environment")
        print(f"  {environment['device_count']} GPU(s), bf16 "
              f"{environment['bf16_supported']}, torch "
              f"{environment['torch_version']}")
        print(f"  vLLM available: {environment['vllm_available']}")
        for smoke in environment["gpu_bf16_matmul_smoke"]:
            print(f"  device {smoke['device']} bf16 matmul: "
                  f"{'ok' if smoke.get('ok') else 'FAILED'}")
        if not environment["environment_ok"]:
            print("\nENVIRONMENT NOT VALID — refusing to continue")
            return 2

    device_map = args.device_map
    if device_map not in ("auto", "balanced"):
        pass

    print("\nSTAGE B/C — checkpoints")
    records = []
    for model_id in args.models:
        print(f"\n=== {model_id} (device_map={device_map})")
        record = stage_bc_checkpoint(model_id, device_map, out_dir)
        records.append(record)
        print(f"  load: {record.get('load_status')}"
              f"{'  — ' + record.get('blocked_reason', '')[:200] if record.get('blocked_reason') else ''}")
        for mode, verdict in (record.get("modes") or {}).items():
            print(f"  {mode:20s} {verdict.get('status')}"
                  f"  answers={verdict.get('answers_non_empty')}/{verdict.get('n')}"
                  f"  leak={verdict.get('marker_leak_into_answer')}"
                  f"  closed={verdict.get('closed_naturally')}"
                  f"  median_r={verdict.get('median_reasoning_tokens')}"
                  f"  {';'.join(verdict.get('problems') or []) or ''}")
        (out_dir / "stage_bc.json").write_text(json.dumps(records, indent=1))

    (out_dir / "stage_bc.json").write_text(json.dumps(records, indent=1))
    print(f"\nwrote {out_dir}/stage_bc.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
