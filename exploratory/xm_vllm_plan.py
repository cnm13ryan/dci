"""Build the design and the engine plan for a vLLM TP=2 run.

Runs in the SCIENTIFIC environment. Emits two files the backend environment
consumes:

    design.jsonl   one line per scientific row: identity, prompt, seed
    plan.json      how to drive the engine for this checkpoint

Nothing model-specific is decided here beyond what `crossmodel.vllm_models`
records, and nothing scientific is decided here at all — the slice comes from
`crossmodel.contract` and the repository's own design builder, exactly as the
Transformers runs did.

`--load 5` selects the repository's EXISTING higher-load construction, taken
from `runs/stageS27_reasoning_k5_.../config.json`:

    --background X_SEMICOLON_FREE,X_ELLIPSIS_FREE,X_PAREN_FREE --load 5
    --permute QAC --fixed-tail U_LEX_FORBID3,U_NUM_MAXINT

i.e. the same QAC contrast with two further background members pinned in a fixed
position. No new difficulty is invented for the k=5 extension.

    uv run python xm_vllm_plan.py --model Qwen/Qwen3.5-4B --load 3 --out runs/DIR
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, seeds, vllm_models

#: The two background members that raise the load from 3 to 5, verbatim from
#: the repository's own k=5 reasoning run. Held in a fixed position by
#: `build_permutation_design(fixed_tail=...)` so raising the load does not also
#: permute instructions the design is not studying.
K5_FIXED_TAIL = ("U_LEX_FORBID3", "U_NUM_MAXINT")

#: Safety margin on the context envelope, as a fraction, matching the canonical
#: natural-reasoning envelope arithmetic.
SAFETY_FRACTION = 0.02


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def calibration_tasks(state, n: int) -> list[dict]:
    """DCI-SHAPED prompts on tasks the evaluation slice never touches.

    Stage B must use the real structural form (A + B/R + background), because
    the previous experiment showed trivial prompts misrepresent reasoning
    behaviour: Gemma 4 declines to open a thought channel on easy questions and
    opens one on composed-constraint questions.
    """
    bank = state.TASKS
    split = bank[bank["split"] == "calibration"]
    if len(split) < n:
        used = {t["task_id"] for t in contract.resolve_tasks(state)}
        split = bank[~bank["task_id"].isin(used)]
    return [{"task_id": r.task_id, "topic": r.topic}
            for r in split.head(n).itertuples()]


def build_rows(state, load: int, stage: str, tasks_override: int | None = None):
    """The frozen slice at k=3, or the repository's k=5 construction."""
    from dci_exploratory import design as design_module

    slice_ = contract.resolve_slice(state)
    fixed_tail = () if load == contract.LOAD else K5_FIXED_TAIL
    tasks = ([dict(t) for t in slice_.tasks] if not tasks_override
             else calibration_tasks(state, tasks_override))
    rows = design_module.build_permutation_design(
        target=slice_.target,
        focals=[slice_.focal, slice_.reference],
        variants=list(slice_.backgrounds),
        tasks=tasks,
        replicates=slice_.replicates,
        base_seed=contract.MASTER_SEED,
        stage=stage,
        paraphrase_id=slice_.paraphrase_id,
        permutations=(slice_.order,),
        fixed_tail=fixed_tail)
    expected = (contract.EXPECTED_ROWS if not tasks_override
                else len(tasks) * slice_.replicates * 4)
    if len(rows) != expected:
        raise ValueError(f"design produced {len(rows)} rows, expected "
                         f"{expected}")
    expected_load = contract.LOAD + len(fixed_tail)
    observed_loads = {r.load for r in rows}
    if observed_loads != {expected_load}:
        raise ValueError(f"rows report load {sorted(observed_loads)}, "
                         f"expected {expected_load}")
    return sorted(rows, key=lambda r: r.row_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True,
                        choices=list(vllm_models.CHECKPOINTS))
    parser.add_argument("--load", type=int, default=contract.LOAD,
                        choices=[3, 5])
    parser.add_argument("--tensor-parallel-size", type=int, default=2)
    parser.add_argument("--max-model-len", type=int, default=None)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--generation-ceiling", type=int, default=8192,
                        help="total tokens per request, reasoning and answer "
                             "together; 0 derives the non-binding envelope "
                             "ceiling from max_model_len instead")
    parser.add_argument("--chunk-size", type=int, default=32)
    parser.add_argument("--deadline-seconds", type=float, default=None)
    parser.add_argument("--cpu-offload-gb", type=float, default=0.0)
    parser.add_argument("--tasks-override", type=int, default=None,
                        help="calibration only: use N disjoint tasks instead "
                             "of the frozen evaluation set")
    args = parser.parse_args()

    from dci_exploratory import extensions, harvest

    extensions.register()
    state = harvest.load()

    spec = vllm_models.get(args.model)
    tag = args.model.split("/")[-1].replace(".", "")
    stage = f"XMV_tp2_k{args.load}"
    out_dir = Path(args.out or f"runs/xmv_{tag}_k{args.load}_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = build_rows(state, args.load, stage, args.tasks_override)
    audit = seeds.assert_seed_regime(rows, contract.MASTER_SEED)

    # -- revision: pinned before anything is generated ----------------------
    revision = args.revision
    if not revision:
        from huggingface_hub import HfApi
        try:
            revision = HfApi().model_info(args.model).sha
        except Exception:                               # noqa: BLE001
            from huggingface_hub.constants import HF_HUB_CACHE
            folder = (Path(HF_HUB_CACHE)
                      / ("models--" + args.model.replace("/", "--"))
                      / "snapshots")
            snaps = [p.name for p in folder.iterdir()
                     if p.is_dir() and len(p.name) == 40] if folder.is_dir() else []
            if len(snaps) != 1:
                raise RuntimeError(
                    f"{args.model}: cannot pin an exact revision (hub "
                    f"unreachable, {len(snaps)} cached snapshots)")
            revision = snaps[0]
    if not revision or len(revision) != 40:
        raise RuntimeError(f"{args.model}: revision {revision!r} is not a sha")

    # -- design file --------------------------------------------------------
    system_message = state.SYSTEM_MESSAGE
    design_path = out_dir / "design.jsonl"
    with design_path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps({
                "row_id": row.row_id, "task_id": row.task_id,
                "replicate": row.replicate, "arm": row.arm,
                "variant": row.variant, "order": row.order,
                "measured": row.measured, "load": row.load,
                "paraphrase_id": row.paraphrase_id, "pair_key": row.pair_key,
                "condition": row.condition, "topic": row.topic,
                "ordered_ids": list(row.ordered_ids),
                "user_prompt": row.user_prompt,
                "system_message": system_message,
                "scientific_seed": seeds.seed_for_row(
                    row, contract.MASTER_SEED, seeds.REASONING_PHASE),
                "answer_seed": seeds.seed_for_row(
                    row, contract.MASTER_SEED, seeds.ANSWER_PHASE),
            }) + "\n")

    # -- engineering envelope ----------------------------------------------
    # Approximate: the exact prompt length depends on the chat template, which
    # only the backend environment can render. A generous allowance is taken
    # here and the backend records the realised lengths.
    max_model_len = args.max_model_len or spec.max_model_len
    longest_user = max(len(r.user_prompt) for r in rows) // 3 + 200
    safety = int(max_model_len * SAFETY_FRACTION)
    envelope_ceiling = (max_model_len - longest_user - contract.ANSWER_TOKENS
                        - safety)
    if envelope_ceiling <= 0:
        raise ValueError("context envelope leaves no room for reasoning")

    # Two different numbers, deliberately kept apart. The ENVELOPE ceiling is
    # what the context window allows and is chosen never to bind. The BOUNDED
    # ceiling is a practical execution limit that WILL bind on some requests —
    # so it is named as such, it is recorded on every row, and the rate at
    # which requests reach it is a reported outcome rather than a footnote.
    if args.generation_ceiling:
        generation_ceiling = args.generation_ceiling
        if generation_ceiling > envelope_ceiling + contract.ANSWER_TOKENS:
            raise ValueError(
                f"generation ceiling {generation_ceiling} exceeds what the "
                f"{max_model_len}-token context leaves for generation")
        ceiling = generation_ceiling - contract.ANSWER_TOKENS
        reasoning_mode = contract.ReasoningMode.THINKING_ENABLED_BOUNDED
    else:
        ceiling = envelope_ceiling
        generation_ceiling = ceiling + contract.ANSWER_TOKENS
        reasoning_mode = contract.ReasoningMode.NATURAL_REASONING

    plan = {
        "stamp": "EXPLORATORY_NO_EVIDENCE",
        "created_utc": utc_stamp(),
        "experiment": "VLLM_TP2_CROSS_MODEL",
        "stage": stage,
        "model_id": args.model,
        "model_revision": revision,
        "model_family": spec.family,
        "backend": "vllm",
        "tensor_parallel_size": args.tensor_parallel_size,
        "dtype": "bfloat16",
        "quantization": "none",
        "disable_custom_all_reduce": True,
        "enforce_eager": True,
        "trust_remote_code": spec.trust_remote_code,
        "limit_mm_per_prompt": spec.limit_mm_per_prompt,
        "max_model_len": max_model_len,
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "cpu_offload_gb": args.cpu_offload_gb,
        "engineering_ceiling": ceiling,
        "envelope_ceiling": envelope_ceiling,
        "generation_ceiling": generation_ceiling,
        "chunk_size": args.chunk_size,
        "deadline_seconds": args.deadline_seconds,
        "answer_tokens": contract.ANSWER_TOKENS,
        "temperature": contract.TEMPERATURE,
        "top_p": contract.TOP_P,
        "top_k": contract.TOP_K,
        "reasoning_mode": reasoning_mode,
        "reasoning_parser": spec.reasoning_parser,
        "chat_template_kwargs": spec.chat_template_kwargs,
        "think_open": spec.think_open,
        "think_close": spec.think_close,
        "load": args.load,
        "expected_rows": len(rows),
        "seed_audit": audit,
        "contract": contract.as_dict(state),
        "notes": spec.notes,
    }
    (out_dir / "plan.json").write_text(json.dumps(plan, indent=1))

    print(f"{args.model} @ {revision}")
    print(f"  k={args.load}  rows={len(rows)}  "
          f"unique seeds={audit['unique_scientific_seeds']}")
    print(f"  parser={spec.reasoning_parser or 'delimiters'}  "
          f"template_kwargs={spec.chat_template_kwargs}")
    print(f"  max_model_len={max_model_len}  mode={reasoning_mode}")
    print(f"  generation ceiling={generation_ceiling} tokens/request "
          f"(reasoning {ceiling} + answer {contract.ANSWER_TOKENS}); "
          f"envelope would allow {envelope_ceiling}")
    print(f"  wrote {design_path} and {out_dir}/plan.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
