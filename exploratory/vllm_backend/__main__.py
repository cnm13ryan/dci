"""Canonical backend CLI. Runs in the vLLM environment, alone.

    python -m vllm_backend --plan runs/DIR/plan.json \
                           --design runs/DIR/design.jsonl \
                           --out runs/DIR/rows.jsonl

Replaces the hand-rolled `main()` of `crossmodel/vllm_tp2.py` and the five
`sys.argv`-parsing scripts under this package. Chunk appending, the wall-clock
deadline and the provenance sidecar behave exactly as they did.

Everything is inside `main()` under a `__main__` guard because vLLM forces the
`spawn` start method on ROCm (fork is unsupported there), so this module is
re-imported in every worker; unguarded top-level work raises "An attempt has
been made to start a new process before the current process has finished its
bootstrapping phase."
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vllm_backend", description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--chunk-size", type=int, default=None,
                        help="requests per llm.generate call; each chunk is "
                             "appended as it finishes")
    parser.add_argument("--deadline-seconds", type=float, default=None,
                        help="whole-run wall-clock backstop; rows past it are "
                             "written NOT_GENERATED")
    parser.add_argument("--strategy", default=None,
                        choices=["single_phase", "two_phase_splice"])
    parser.add_argument("--no-verify-switch", action="store_true",
                        help="skip the chat-template switch liveness check "
                             "(diagnostics only; never for a scientific run)")
    args = parser.parse_args(argv)

    from dataclasses import replace

    from vllm_backend import engine, io

    engine_plan, sampling, run_plan, card, raw = io.load_plan(args.plan)
    requests = io.load_design(args.design)

    if args.chunk_size:
        run_plan = replace(run_plan, chunk_size=args.chunk_size)
    if args.deadline_seconds is not None:
        run_plan = replace(run_plan, deadline_seconds=args.deadline_seconds)
    if args.strategy:
        run_plan = replace(run_plan, strategy=args.strategy)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("")                       # a resumed run starts clean

    written = {"n": 0}

    def on_chunk(chunk):
        io.write_rows(out, chunk, append=True)
        written["n"] += len(chunk)
        answered = sum(1 for r in chunk if r.final_answer.strip())
        print(f"  +{len(chunk)} rows ({answered} answered), "
              f"{written['n']}/{len(requests)} total", flush=True)

    outcome = engine.run(engine_plan, sampling, run_plan, card, requests,
                         on_chunk=on_chunk,
                         verify_switch=not args.no_verify_switch)
    provenance = outcome["provenance"]
    provenance["plan_source"] = str(args.plan)
    provenance["expected_rows"] = raw.get("expected_rows", len(requests))
    io.write_provenance(out, provenance)

    summary = provenance.get("summary") or {}
    print(f"\n{engine_plan.model_id} · TP={engine_plan.tensor_parallel_size} "
          f"· {summary.get('rows', 0)} rows")
    print(f"  parser {provenance.get('reasoning_parser_used', 'n/a')}")
    print(f"  outcomes {json.dumps(summary.get('by_outcome', {}))}")
    print(f"  reasoning emitted {summary.get('reasoning_emitted', 0)}"
          f" · cap hits {summary.get('reasoning_cap_hits', 0)}"
          f" · empty answers {summary.get('empty_answers', 0)}")
    print(f"  wrote {out}")

    if provenance.get("blocked"):
        return 2
    # Non-zero when the engineering ceiling bound, matching the old contract.
    return 1 if summary.get("reasoning_cap_hits") else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(3)
