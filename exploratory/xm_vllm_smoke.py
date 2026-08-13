"""Stage A: TP=2 qualification for one checkpoint under vLLM.

Loads the checkpoint with `tensor_parallel_size=2`, generates four trivial and
four composed-constraint prompts with native thinking explicitly enabled, and
answers the questions that must be settled before any DCI prompt is run:

* does the engine start on two gfx1100 cards at all;
* do BOTH cards hold model state, or is rank 1 idle while rank 0 holds
  everything — the difference between real tensor parallelism and a single-GPU
  run wearing a TP label;
* does the reasoning parser separate reasoning from answer;
* is the answer free of reasoning markers and chat-control markup;
* and does the checkpoint answer trivial questions correctly, which is a
  CORRUPTION detector rather than a capability test. The previous attempt found
  a Gemma class that loaded with randomly initialised weights and emitted
  fluent multilingual noise without raising; nothing about that failure was
  specific to Transformers, so vLLM is subjected to the same gate.

Classifies TP2_LOAD_VALID / TP2_BACKEND_BLOCKED / TP2_MODEL_UNSUPPORTED /
TP2_REASONING_INVALID / TP2_OUTPUT_INVALID.

    uv run python xm_vllm_smoke.py --model Qwen/Qwen3.5-4B
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, vllm_models

#: These rows are the BACKEND record, straight out of
#: `raw_generations.jsonl` — not the scored row the ingest builds. The two
#: schemas differ deliberately and this file reads the first: `reasoning_closed`
#: here becomes `natural_reasoning_closed` only after `xm_vllm_ingest`.
TECHNICAL_FAILURE = "TECHNICAL_FAILURE"

HERE = Path(__file__).resolve().parent
BACKEND_PYTHON = HERE / ".venv-vllm" / "bin" / "python"
#: The canonical backend, invoked as a MODULE. `-m` resolves the package from
#: the working directory, so the subprocess below runs with cwd=HERE; that is
#: what the deleted `crossmodel/vllm_tp2.py` shim used to arrange by inserting
#: the path itself. Pinned by tests/test_backend_cli_contract.py.
BACKEND_COMMAND = ("-m", "vllm_backend")

#: Trivial prompts carry an expected substring: a weight-integrity check, not a
#: capability benchmark. Composed prompts are what actually elicit reasoning —
#: Gemma 4 declines to open a thought channel on easy questions, so a smoke set
#: of only trivial prompts cannot qualify a reasoning interface at all. All are
#: disjoint from the DCI task bank.
SMOKE = [
    ("Name the capital city of Japan.", "tokyo"),
    ("What is 17 plus 25?", "42"),
    ("List the first three prime numbers.", "5"),
    ("What colour is a clear daytime sky?", "blue"),
    ("Write exactly three sentences about bicycles, each one longer than the "
     "last, and use exactly one comma in the whole answer.", None),
    ("Write exactly two sentences about rain; use exactly one semicolon in "
     "the whole answer.", None),
    ("List the first three prime numbers, then explain in exactly two "
     "sentences why the first of them is prime.", None),
    ("Write exactly four sentences about tea, each beginning with a word "
     "whose first letter is T.", None),
]

#: Chat-control markup of the shapes these families use. Matching on SHAPE
#: rather than a token list makes this a check on the cleaning, not a
#: restatement of it.
CONTROL_RESIDUE = re.compile(r"<\|[^>]{0,40}\|?>|<[^<>]{0,40}\|>|◁/?[a-z]+▷")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True,
                        choices=list(vllm_models.CHECKPOINTS))
    parser.add_argument("--tensor-parallel-size", type=int, default=2)
    parser.add_argument("--max-model-len", type=int, default=8192)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    from dci_exploratory import extensions, harvest

    extensions.register()
    state = harvest.load()
    spec = vllm_models.get(args.model)

    tag = args.model.split("/")[-1].replace(".", "")
    # RESOLVED. The backend runs with cwd=exploratory so that `-m vllm_backend`
    # can find the package, and the default here is RELATIVE ("runs/..."), so an
    # unresolved path would be written by this driver relative to $PWD and read
    # by the backend relative to exploratory/. Absolute paths make the working
    # directory irrelevant to where generations land.
    out_dir = Path(args.out or f"runs/xmv_smoke_{tag}_{utc_stamp()}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # -- revision -----------------------------------------------------------
    from huggingface_hub import HfApi
    from huggingface_hub.constants import HF_HUB_CACHE
    try:
        revision = HfApi().model_info(args.model).sha
    except Exception:                                   # noqa: BLE001
        folder = (Path(HF_HUB_CACHE)
                  / ("models--" + args.model.replace("/", "--")) / "snapshots")
        snaps = [p.name for p in folder.iterdir()
                 if p.is_dir() and len(p.name) == 40] if folder.is_dir() else []
        revision = snaps[0] if len(snaps) == 1 else None
    if not revision or len(revision) != 40:
        print(f"{args.model}: cannot pin an exact revision")
        return 2

    with (out_dir / "design.jsonl").open("w") as handle:
        for i, (text, _) in enumerate(SMOKE):
            handle.write(json.dumps({
                "row_id": f"smoke{i:02d}", "user_prompt": text,
                "system_message": state.SYSTEM_MESSAGE,
                "scientific_seed": 100000 + i, "answer_seed": 200000 + i,
            }) + "\n")

    plan = {
        "model_id": args.model, "model_revision": revision,
        "model_family": spec.family, "backend": "vllm",
        "tensor_parallel_size": args.tensor_parallel_size,
        "dtype": "bfloat16", "quantization": "none",
        "disable_custom_all_reduce": True, "enforce_eager": True,
        "trust_remote_code": spec.trust_remote_code,
        "limit_mm_per_prompt": spec.limit_mm_per_prompt,
        "max_model_len": args.max_model_len,
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "engineering_ceiling": args.max_model_len - 1024,
        "answer_tokens": contract.ANSWER_TOKENS,
        "temperature": contract.TEMPERATURE, "top_p": contract.TOP_P,
        "top_k": contract.TOP_K, "reasoning_mode": "NATURAL_REASONING",
        "reasoning_parser": spec.reasoning_parser,
        "chat_template_kwargs": spec.chat_template_kwargs,
        "think_open": spec.think_open, "think_close": spec.think_close,
    }
    (out_dir / "plan.json").write_text(json.dumps(plan, indent=1))

    # -- run the backend ----------------------------------------------------
    command = [str(BACKEND_PYTHON), *BACKEND_COMMAND,
               "--plan", str(out_dir / "plan.json"),
               "--design", str(out_dir / "design.jsonl"),
               "--out", str(out_dir / "raw_generations.jsonl")]
    print(" ".join(command), flush=True)
    # Streamed, not captured. vLLM writes its startup and progress to stderr,
    # and a captured pipe only appears when the process exits — which makes a
    # long generation indistinguishable from a hang while it runs.
    log_path = out_dir / "backend.log"
    with log_path.open("w") as handle:
        completed = subprocess.run(command, stdout=handle,
                                   stderr=subprocess.STDOUT, cwd=str(HERE))
    blob_text = log_path.read_text(errors="ignore")

    record: dict = {"model_id": args.model, "model_revision": revision,
                    "tensor_parallel_size": args.tensor_parallel_size,
                    "checked_utc": utc_stamp(),
                    "reasoning_parser": spec.reasoning_parser,
                    "chat_template_kwargs": spec.chat_template_kwargs,
                    "returncode": completed.returncode}

    raw_path = out_dir / "raw_generations.jsonl"
    if not raw_path.exists():
        blob = blob_text
        lowered = blob.lower()
        if "not supported" in lowered or "are not supported" in lowered:
            status = "TP2_MODEL_UNSUPPORTED"
        elif "out of memory" in lowered:
            status = "TP2_CAPACITY_BLOCKED"
        else:
            status = "TP2_BACKEND_BLOCKED"
        record["status"] = status
        record["error_tail"] = blob[-2500:]
        (out_dir / "smoke.json").write_text(json.dumps(record, indent=1))
        print(f"  {status}")
        print(blob[-1200:])
        return 1

    rows = [json.loads(l) for l in raw_path.open()]
    engine = json.loads((out_dir / "raw_generations_engine.json").read_text())
    record["engine"] = engine

    answers = [r["final_answer"] for r in rows]
    expected = [want for _, want in SMOKE]
    checks = sum(1 for w in expected if w)
    passed = sum(1 for a, w in zip(answers, expected)
                 if w and w in a.lower())
    markers = [spec.think_open, spec.think_close]

    record.update({
        "n": len(rows),
        "answers_non_empty": sum(1 for a in answers if a.strip()),
        "reasoning_emitted": sum(1 for r in rows if r["reasoning_emitted"]),
        "closed": sum(1 for r in rows if r["reasoning_closed"]),
        "cap_hits": sum(1 for r in rows if r["reasoning_cap_hit"]),
        "truncated": sum(1 for r in rows if r["answer_truncated"]),
        "technical_failures": sum(1 for r in rows
                                if r["outcome"] == TECHNICAL_FAILURE),
        "marker_leak_into_answer": sum(
            1 for a in answers if any(m in a for m in markers)),
        "control_token_residue": sum(
            1 for a in answers if CONTROL_RESIDUE.search(a)),
        "weight_integrity_checks": checks,
        "weight_integrity_passed": passed,
        "median_reasoning_tokens": sorted(
            r["reasoning_tokens"] for r in rows)[len(rows) // 2],
        "max_reasoning_tokens": max(r["reasoning_tokens"] for r in rows),
    })

    problems = []
    if record["technical_failures"]:
        problems.append("technical failure during generation")
    if record["answers_non_empty"] != record["n"]:
        problems.append("empty final answer")
    if record["marker_leak_into_answer"]:
        problems.append("reasoning marker inside the final answer")
    if record["control_token_residue"]:
        problems.append("chat-control markup inside the final answer")
    if passed == 0:
        problems.append("WEIGHTS SUSPECT — no trivial question answered "
                        "correctly, which is what a corrupt load looks like")
    if record["reasoning_emitted"] == 0:
        problems.append("no reasoning was emitted on any prompt")
    unclosed = record["reasoning_emitted"] - record["closed"]
    if unclosed:
        problems.append(f"{unclosed} trace(s) opened but never closed")

    if passed == 0:
        record["status"] = "TP2_OUTPUT_INVALID"
    elif problems and any("marker" in p or "markup" in p or "closed" in p
                          for p in problems):
        record["status"] = "TP2_REASONING_INVALID"
    elif problems:
        record["status"] = "TP2_OUTPUT_INVALID"
    else:
        record["status"] = "TP2_LOAD_VALID"
    record["problems"] = problems

    (out_dir / "smoke.json").write_text(json.dumps(record, indent=1))
    print(f"\n  {record['status']}")
    print(f"  answers {record['answers_non_empty']}/{record['n']} · "
          f"reasoning emitted {record['reasoning_emitted']} · "
          f"closed {record['closed']} · cap hits {record['cap_hits']}")
    print(f"  weight integrity {passed}/{checks} · marker leak "
          f"{record['marker_leak_into_answer']} · control residue "
          f"{record['control_token_residue']}")
    print(f"  median reasoning {record['median_reasoning_tokens']} · max "
          f"{record['max_reasoning_tokens']}")
    if problems:
        print("  problems: " + "; ".join(problems))
    print(f"  wrote {out_dir}/")
    return 0 if record["status"] == "TP2_LOAD_VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
