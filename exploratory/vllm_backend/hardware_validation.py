"""Hardware validation for the canonical backend, with a retained artifact.

The consolidation was reported as hardware-validated and left no evidence, so
the claim could not be checked. This script is the replacement: it drives every
case through `engine.run` -- the same entry real experiments use -- and writes a
JSON record of exactly what ran, on which revision, under which wheel, on which
cards, with which decoding, and what came back.

Run it from the vLLM environment, which is the one that can build an engine:

    VLLM=/path/to/vllm/venv/bin/python
    $VLLM -m vllm_backend.hardware_validation --out HARDWARE_VALIDATION.json

Nothing here is a unit test. It reads weights, occupies both cards, and takes
minutes per case. `--only` selects a subset by name so a single case can be
re-run after a fix without paying for the rest.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vllm_backend import engine                                   # noqa: E402
from vllm_backend.contract import GenerationRequest, Outcome      # noqa: E402
from vllm_backend.hardware import probe as probe_host             # noqa: E402
from vllm_backend.registry import (ReasoningMode, get,            # noqa: E402
                                   get_or_default)
from vllm_backend.resolve import (resolve_engine, resolve_run,    # noqa: E402
                                  resolve_sampling)

#: Pinned exactly as the study pins them. A validation run on a different
#: revision validates a different checkpoint.
REVISIONS = {
    "Qwen/Qwen3-4B": "1cfa9a7208912126459214e8b04321603b3df60c",
    "Qwen/Qwen3-4B-Thinking-2507": "",
    "Qwen/Qwen2.5-0.5B-Instruct": "7ae557604adf67be50417f59c2c2f167def9a775",
}

PROMPT = ("Explain how a corkscrew removes a cork. "
          "Write exactly 4 sentences.")


@dataclass
class Case:
    name: str
    model_id: str
    mode: str
    tensor_parallel_size: int = 1
    strategy: str = ""
    max_tokens: int = 96
    reasoning_budget: int = 0
    expect_outcome: str = Outcome.OK.value
    note: str = ""


CASES: list[Case] = [
    Case("qwen3_no_thinking", "Qwen/Qwen3-4B", ReasoningMode.NO_THINKING,
         note="the b=0 control arm; the condition the missing card destroyed"),
    Case("qwen3_natural", "Qwen/Qwen3-4B", ReasoningMode.NATURAL_REASONING,
         max_tokens=512, note="the natural endpoint"),
    Case("qwen3_limited", "Qwen/Qwen3-4B", ReasoningMode.LIMITED_REASONING,
         max_tokens=512, reasoning_budget=256, strategy="two_phase_splice",
         note="capped ladder AND the two_phase_splice strategy"),
    Case("qwen3_thinking_preopen", "Qwen/Qwen3-4B-Thinking-2507",
         ReasoningMode.NATURAL_REASONING, max_tokens=512,
         note="the checkpoint whose template pre-opens <think>; exercises the "
              "split repair on the exact case it exists for"),
    Case("qwen25_tp1", "Qwen/Qwen2.5-0.5B-Instruct", ReasoningMode.NO_THINKING,
         tensor_parallel_size=1, note="single card"),
    Case("qwen25_tp2", "Qwen/Qwen2.5-0.5B-Instruct", ReasoningMode.NO_THINKING,
         tensor_parallel_size=2, note="both cards must participate"),
    Case("unsupported_checkpoint", "not-a-real/checkpoint",
         ReasoningMode.NO_THINKING,
         expect_outcome=Outcome.BACKEND_UNSUPPORTED.value,
         note="the failure path: an unknown checkpoint must be REFUSED, and "
              "refused as a result rather than a crash"),
]


def rocm_versions() -> dict[str, Any]:
    out: dict[str, Any] = {"python": platform.python_version()}
    try:
        import torch
        out["torch"] = torch.__version__
        out["hip"] = getattr(torch.version, "hip", None)
        out["devices"] = [torch.cuda.get_device_name(i)
                          for i in range(torch.cuda.device_count())]
    except Exception as error:                          # noqa: BLE001
        out["torch"] = f"unavailable: {error}"
    try:
        import vllm
        out["vllm"] = vllm.__version__
    except Exception as error:                          # noqa: BLE001
        out["vllm"] = f"unavailable: {error}"
    return out


def gpu_memory() -> list[dict[str, Any]]:
    """Per-card VRAM use, so TP=2 can be shown to use BOTH cards."""
    try:
        raw = subprocess.run(["rocm-smi", "--showmemuse", "--json"],
                             capture_output=True, text=True, timeout=30).stdout
        data = json.loads(raw)
    except Exception:                                   # noqa: BLE001
        return []
    return [{"card": card, **{k: v for k, v in values.items()
                              if "memory" in k.lower() or "Memory" in k}}
            for card, values in sorted(data.items())]


def run_case(case: Case) -> dict[str, Any]:
    record: dict[str, Any] = {"case": asdict(case), "started": time.time()}
    request = GenerationRequest(
        row_id=f"{case.name}-1", user_prompt=PROMPT, system_message="",
        scientific_seed=20260813, answer_seed=20260814,
        identity={"case": case.name})
    try:
        card = get(case.model_id)
    except KeyError as error:
        # An unregistered checkpoint must not be silently defaulted. Recorded
        # as the refusal it is.
        record.update(outcome="REGISTRY_REFUSED", detail=str(error)[:300],
                      ok=case.expect_outcome != Outcome.OK.value)
        return record

    host = probe_host()
    revision = REVISIONS.get(case.model_id, "")
    try:
        engine_plan = resolve_engine(card, host, {
            "tensor_parallel_size": case.tensor_parallel_size,
            "model_revision": revision})
        run_plan = resolve_run(card, case.mode,
                               strategy=case.strategy or "single_phase")
        # The capped ladder stops phase 1 at the close delimiter; that stop
        # string is what makes the budget a budget.
        stop = ((card.think_close,) if case.strategy == "two_phase_splice"
                else ())
        sampling = resolve_sampling(
            case.reasoning_budget or case.max_tokens,
            answer_tokens=case.max_tokens, stop=stop)
    except Exception as error:                          # noqa: BLE001
        record.update(outcome="PLAN_FAILED",
                      detail=f"{type(error).__name__}: {error}"[:400], ok=False)
        return record

    memory_before = gpu_memory()
    try:
        outcome = engine.run(engine_plan, sampling, run_plan, card, [request])
    except Exception as error:                          # noqa: BLE001
        record.update(outcome="RAISED",
                      detail=f"{type(error).__name__}: {error}"[:600], ok=False)
        return record

    result = outcome["results"][0]
    provenance = outcome.get("provenance", {})
    switch = provenance.get("switch_evidence", {})
    record.update(
        outcome=result.outcome,
        detail=result.outcome_detail[:300],
        ok=result.outcome == case.expect_outcome,
        engine_kwargs={k: str(v) for k, v in engine_plan.engine_kwargs().items()},
        sampling={"temperature": sampling.temperature, "top_p": sampling.top_p,
                  "top_k": sampling.top_k, "max_tokens": case.max_tokens},
        strategy=run_plan.strategy,
        reasoning={
            "emitted": result.reasoning_emitted,
            "closed": result.reasoning_closed,
            "cap_hit": result.reasoning_cap_hit,
            "tokens": result.reasoning_tokens,
            "channel_valid": result.channel_valid,
            # The leak signature: a marker surviving into the scored answer.
            "markers_in_answer": any(
                m in result.final_answer
                for m in ("<think>", "</think>", "◁think▷", "◁/think▷")),
        },
        answer_preview=result.final_answer[:200],
        answer_tokens=result.final_answer_tokens,
        template={"acquisition": switch.get("card", {}).get(
                      "tokenizer_acquisition"),
                  "revision": switch.get("card", {}).get("tokenizer_revision"),
                  "modes_render_distinctly": switch.get("card", {}).get(
                      "modes_render_distinctly"),
                  "modes_sharing_a_prompt": switch.get("card", {}).get(
                      "modes_sharing_a_prompt")},
        memory_before=memory_before, memory_after=gpu_memory(),
        elapsed_seconds=round(time.time() - record["started"], 1))
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="HARDWARE_VALIDATION.json")
    parser.add_argument("--only", nargs="*", default=None,
                        help="case names; default is all")
    args = parser.parse_args(argv)

    cases = [c for c in CASES if not args.only or c.name in args.only]
    report: dict[str, Any] = {
        "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"node": platform.node(), "kernel": platform.release()},
        "versions": rocm_versions(),
        "revisions": REVISIONS,
        "prompt": PROMPT,
        "cases": [],
    }
    for case in cases:
        print(f"\n=== {case.name}: {case.model_id} {case.mode} "
              f"TP={case.tensor_parallel_size}", flush=True)
        record = run_case(case)
        report["cases"].append(record)
        print(f"    -> {record.get('outcome')} ok={record.get('ok')} "
              f"({record.get('elapsed_seconds', '?')}s)", flush=True)

    report["passed"] = sum(1 for c in report["cases"] if c.get("ok"))
    report["total"] = len(report["cases"])
    Path(args.out).write_text(json.dumps(report, indent=1, default=str))
    print(f"\nwrote {args.out}: {report['passed']}/{report['total']} as expected")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
