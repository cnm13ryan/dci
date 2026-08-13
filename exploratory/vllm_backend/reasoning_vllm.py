"""Reasoning-budget grid on vLLM, channels kept apart. Backend venv only.

The reasoning channel is NEVER part of the response. Phase 1 thinks under the
assigned budget `b`; phase 2 answers under a budget that is identical in every
treatment, so the verifier sees a comparable surface at every b.

`b = 0` is the model's OWN non-thinking mode (`enable_thinking=False`), not a
zero-length truncation — that makes the bottom of the grid a native condition
rather than an interruption.

Nothing is scored here. Scoring happens in the study venv against the registry,
from the saved answer field.

Engine construction, sampling, chat rendering and the record schema come from
`vllm_backend`; this file now contains ONLY the grid, which is the part that is
actually specific to this experiment.

    python vllm_backend/reasoning_vllm.py MODEL REVISION 0,256,1024 DESIGN OUT [ANSWER_TOKENS]
"""
from __future__ import annotations

import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vllm_backend import engine, io, records
from vllm_backend.hardware import probe as probe_host
from vllm_backend.reasoning import build_parser
from vllm_backend.registry import ReasoningMode, get
from vllm_backend.resolve import (
    resolve_engine,
    resolve_run,
    resolve_sampling,
)

#: One seed PER ROW, not one per batch. A single shared seed makes two replicate
#: rows of the same task byte-identical, so "2 replicates" silently becomes one
#: draw counted twice. Deriving the seed from row position within the design
#: keeps replicates distinct and keeps every run reproducible.
SEED_BASE = 20260810
SEED_STRIDE = 7919


def row_seeds(n: int, offset: int) -> list[int]:
    return [SEED_BASE + offset + SEED_STRIDE * i for i in range(n)]


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    model_id, revision = argv[0], argv[1]
    budgets = [int(b) for b in argv[2].split(",")]
    design_path, out_path = Path(argv[3]), Path(argv[4])
    answer_tokens = int(argv[5]) if len(argv) > 5 else 512

    # `get`, not `get_or_default`: this is an experiment runner, and the
    # fallback card cannot say how a checkpoint selects its reasoning mode.
    # Reaching for it here is what silently dropped `enable_thinking`.
    card = replace(get(model_id), model_id=model_id)
    host = probe_host()
    engine_plan = resolve_engine(card, host, {
        "tensor_parallel_size": 2, "max_model_len": 16384,
        "seed": SEED_BASE, "model_revision": revision})
    llm, tokenizer, load_seconds = engine.build_engine(engine_plan)
    parser, parser_label = build_parser(card.reasoning_parser, tokenizer,
                                        card.think_open, card.think_close)

    base_rows = io.load_design(design_path)
    all_results, budget_meta = [], []

    for budget in budgets:
        started = time.perf_counter()
        thinking = budget > 0
        mode = (ReasoningMode.LIMITED_REASONING if thinking
                else ReasoningMode.NO_THINKING)
        run_plan = resolve_run(card, mode,
                               strategy="two_phase_splice" if thinking
                               else "single_phase")
        seeds = row_seeds(len(base_rows), 0)
        answer_seeds = row_seeds(len(base_rows), 1)
        requests = [
            replace(r, scientific_seed=s, answer_seed=a,
                    identity={**r.identity, "reasoning_budget": budget,
                              "native_nonthinking": not thinking})
            for r, s, a in zip(base_rows, seeds, answer_seeds)]

        template_kwargs = run_plan.chat_template_kwargs
        # NOT guarded on `template_kwargs` being non-empty: an empty mapping
        # is exactly the case that used to disable this check silently.
        if requests:
            engine.verify_template_switch(
                tokenizer, requests[0], template_kwargs, card,
                run_plan.reasoning_mode)
        prompts = [engine.render_prompt(tokenizer, r, template_kwargs)
                   for r in requests]

        # b == 0 is the native non-thinking condition: ONE generation under the
        # fixed answer allowance, never a truncated thinking run.
        sampling = resolve_sampling(
            max_tokens=budget if thinking else answer_tokens,
            answer_tokens=answer_tokens)
        strategy = engine.STRATEGIES[run_plan.strategy]
        chunk = strategy(llm, tokenizer, requests, prompts, sampling, parser, card)

        all_results.extend(chunk)
        elapsed = time.perf_counter() - started
        summary = records.summarise(chunk)
        budget_meta.append({"budget": budget, "seconds": round(elapsed, 1),
                            "mode": mode, **summary})
        closed = sum(1 for r in chunk if r.reasoning_closed) or 0
        mean_reasoning = (sum(r.reasoning_tokens for r in chunk) / len(chunk)
                          if chunk else 0.0)
        print(f"b={budget:>5}  {len(chunk)} rows  {elapsed:6.1f}s  "
              f"closed={closed / max(len(chunk), 1):.3f}  "
              f"mean_reasoning={mean_reasoning:7.1f}  "
              f"empty_answers={summary['empty_answers']}  "
              f"truncated={summary['answers_truncated']}", flush=True)

    io.write_rows(out_path, all_results)
    io.write_provenance(out_path, {
        "experiment": "REASONING_BUDGET_GRID",
        "engine_kwargs": {k: str(v) for k, v in engine_plan.engine_kwargs().items()},
        "reasoning_parser_used": parser_label,
        "budgets": budgets, "answer_tokens": answer_tokens,
        "per_budget": budget_meta, "load_seconds": round(load_seconds, 1),
        "host": host.to_dict(), "summary": records.summarise(all_results),
    })
    print("wrote", out_path, len(all_results), "records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
