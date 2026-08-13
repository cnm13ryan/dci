"""The NATURAL_REASONING condition: let the model finish thinking on its own.

Every other reasoning condition in this study deliberately caps the thinking
phase. This one does not. The only limit is an engineering ceiling derived from
what actually fits in the context window, and the run is only valid if that
ceiling is never reached:

    ceiling = context_limit
              - longest_rendered_prompt
              - answer_allowance          (identical to every other condition)
              - control_tokens            (the close-delimiter splice)
              - safety_margin             (2% of the context window)

The number is whatever that arithmetic gives. It is deliberately NOT a round
power of two: a round number would be a guess about how much room is enough,
and the requirement here is a limit derived from the envelope that the model
almost never touches.

"Natural" means only this: the experiment did not stop the model's reasoning
before it finished. It does not mean unlimited compute or unlimited context.

The arithmetic now lives in `vllm_backend.resolve.context_envelope`; engine,
sampling and schema come from `vllm_backend`.

    python vllm_backend/natural_reasoning.py MODEL REVISION DESIGN OUT [ANSWER_TOKENS]
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
from vllm_backend.registry import ReasoningMode, get_or_default
from vllm_backend.resolve import (
    context_envelope,
    resolve_engine,
    resolve_run,
    resolve_sampling,
)

CONTEXT_LIMIT = 40960          # practical envelope, read from the config
SAFETY_FRACTION = 0.02         # reserve 2% rather than trust the edge
#: Offset that keeps this condition's seeds disjoint from every other run.
SEED_OFFSET = 90000
SEED_BASE = 20260810
SEED_STRIDE = 7919


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    model_id, revision = argv[0], argv[1]
    design_path, out_path = Path(argv[2]), Path(argv[3])
    answer_tokens = int(argv[4]) if len(argv) > 4 else 512

    card = replace(get_or_default(model_id), model_id=model_id)
    host = probe_host()
    engine_plan = resolve_engine(card, host, {
        "tensor_parallel_size": 2, "max_model_len": CONTEXT_LIMIT,
        "seed": SEED_BASE, "model_revision": revision})
    llm, tokenizer, load_seconds = engine.build_engine(engine_plan)
    parser, parser_label = build_parser(card.reasoning_parser, tokenizer,
                                        card.think_open, card.think_close)

    run_plan = resolve_run(card, ReasoningMode.NATURAL_REASONING,
                           strategy="two_phase_splice")
    base_rows = io.load_design(design_path)
    requests = [
        replace(r,
                scientific_seed=SEED_BASE + SEED_OFFSET + SEED_STRIDE * i,
                answer_seed=SEED_BASE + SEED_OFFSET + 1 + SEED_STRIDE * i,
                identity={**r.identity, "condition": "NATURAL_REASONING"})
        for i, r in enumerate(base_rows)]

    template_kwargs = run_plan.chat_template_kwargs
    if requests and template_kwargs:
        engine.verify_template_switch(tokenizer, requests[0], template_kwargs)
    prompts = [engine.render_prompt(tokenizer, r, template_kwargs)
               for r in requests]

    prompt_tokens = [len(tokenizer.encode(p, add_special_tokens=False))
                     for p in prompts]
    control_tokens = len(tokenizer.encode(f"{card.think_close}\n\n",
                                          add_special_tokens=False))
    ceiling = context_envelope(CONTEXT_LIMIT, max(prompt_tokens), answer_tokens,
                               control_tokens, SAFETY_FRACTION)
    envelope = {
        "context_limit": CONTEXT_LIMIT,
        "longest_prompt_tokens": max(prompt_tokens),
        "median_prompt_tokens": sorted(prompt_tokens)[len(prompt_tokens) // 2],
        "answer_allowance": answer_tokens, "control_tokens": control_tokens,
        "safety_fraction": SAFETY_FRACTION, "derived_ceiling": ceiling,
    }
    print("engineering envelope:", envelope, flush=True)

    requests = [replace(r, identity={**r.identity, "reasoning_budget": ceiling,
                                     "engineering_ceiling": ceiling})
                for r in requests]

    started = time.perf_counter()
    sampling = resolve_sampling(max_tokens=ceiling, answer_tokens=answer_tokens)
    results = engine.generate_two_phase_splice(
        llm, tokenizer, requests, prompts, sampling, parser, card)
    elapsed = time.perf_counter() - started

    io.write_rows(out_path, results)
    summary = records.summarise(results)
    io.write_provenance(out_path, {
        "experiment": "NATURAL_REASONING",
        "engine_kwargs": {k: str(v) for k, v in engine_plan.engine_kwargs().items()},
        "reasoning_parser_used": parser_label, **envelope,
        "generation_seconds": round(elapsed, 1),
        "load_seconds": round(load_seconds, 1),
        "host": host.to_dict(), "summary": summary,
    })

    lengths = sorted(r.reasoning_tokens for r in results)
    caps = summary["reasoning_cap_hits"]

    def pct(p: float) -> int:
        return lengths[min(len(lengths) - 1, int(p * len(lengths)))]

    print(f"\nNATURAL_REASONING · {len(results)} rows · ceiling {ceiling}")
    print(f"  reached the ceiling: {caps}/{len(results)}"
          f"{'  <-- INVALID, the ceiling binds' if caps else '  (none — the ceiling never binds)'}")
    if lengths:
        print(f"  reasoning tokens: min {lengths[0]} · p25 {pct(.25)} "
              f"· median {pct(.5)} · p75 {pct(.75)} · p90 {pct(.9)} "
              f"· max {lengths[-1]}")
    print(f"  empty answers: {summary['empty_answers']} · "
          f"truncated: {summary['answers_truncated']}")
    print(f"  generation {elapsed:.1f}s")
    return 1 if caps else 0


if __name__ == "__main__":
    raise SystemExit(main())
