"""How long does this reasoning model actually think on the real DCI prompts?

Uses the REAL stored prompts from an executed run, so the distribution is the one
the experiment would face, not a distribution over toy questions.

Nothing is scored here. The single question is where `</think>` lands when the
budget is not binding, which decides whether a reasoning-budget grid can be
defined at all. The answer channel is kept separate from the first token.
"""
import json
import sys
from dataclasses import replace as _replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vllm_backend import engine as _engine
from vllm_backend.contract import GenerationRequest
from vllm_backend.hardware import probe as _probe_host
from vllm_backend.registry import get_or_default
from vllm_backend.resolve import resolve_engine, resolve_sampling

PROMPTS = Path("nl_prompts.json")

#: Default only; the checkpoint's own delimiter is used at run time
#: via the model card, so a Gemma/Kimi checkpoint is not mis-split.
THINK_CLOSE = "</think>"

#: The engine seed the whole reasoning line runs under. `EnginePlan.seed`
#: defaults to something else, so every script states this explicitly.
ENGINE_SEED = 20260810


def main(argv: list[str] | None = None) -> int:
    # Parsed HERE, not at import. Reading sys.argv at module scope made this the
    # one script in the package that could not be imported -- `int(sys.argv[3])`
    # ran against pytest's own arguments and raised -- so it was also the one
    # script no test could reach. Its siblings all take `argv`.
    argv = list(argv if argv is not None else sys.argv[1:])
    model_id, revision = argv[0], argv[1]
    max_tokens = int(argv[2]) if len(argv) > 2 else 32768
    out_path = Path(argv[3]) if len(argv) > 3 else Path("natural_length.json")

    records = json.loads(PROMPTS.read_text())
    # Engine and decoding come from `vllm_backend`; the diagnostic JSON emitted
    # below is an EXISTING output format and is deliberately unchanged.
    card = _replace(get_or_default(model_id), model_id=model_id)
    plan = resolve_engine(card, _probe_host(), {
        "tensor_parallel_size": 2, "max_model_len": max_tokens + 2048,
        "seed": ENGINE_SEED, "model_revision": revision})
    llm, tok, _load_seconds = _engine.build_engine(plan)

    # This probe asks where the model closes its trace when nothing is
    # steering it, so no chat-template reasoning kwargs are passed.
    requests = [GenerationRequest(row_id=str(r.get("row_id", i)),
                                  user_prompt=r["user_prompt"],
                                  system_message=r.get("system_message", "") or "")
                for i, r in enumerate(records)]
    prompts = [_engine.render_prompt(tok, r, {}) for r in requests]

    params = _engine.build_sampling(
        resolve_sampling(max_tokens=max_tokens), max_tokens, ENGINE_SEED)
    outputs = llm.generate(prompts, params)

    rows = []
    for record, out in zip(records, outputs):
        completion = out.outputs[0]
        text = completion.text
        close = card.think_close or THINK_CLOSE
        closed = close in text
        if closed:
            reasoning, answer = text.split(close, 1)
        else:
            reasoning, answer = text, ""
        # Token-accurate reasoning length, not a character proxy.
        reasoning_tokens = len(tok.encode(reasoning, add_special_tokens=False))
        rows.append({
            "row_id": record.get("row_id"), "task_id": record.get("task_id"),
            "arm": record.get("arm"), "variant": record.get("variant"),
            "closed_naturally": closed,
            "reasoning_tokens": reasoning_tokens,
            "answer_chars": len(answer.strip()),
            "total_tokens": len(completion.token_ids),
            "finish_reason": completion.finish_reason,
            "cap_hit": completion.finish_reason == "length",
            "answer_preview": answer.strip()[:300],
        })
    out_path.write_text(json.dumps(rows, indent=1))

    closed = [r for r in rows if r["closed_naturally"]]
    lengths = sorted(r["reasoning_tokens"] for r in closed)
    print(f"\nmodel={model_id} max_tokens={max_tokens} n={len(rows)}")
    print(f"natural closure: {len(closed)}/{len(rows)} = {len(closed)/len(rows):.3f}")
    if lengths:
        def pct(p):
            return lengths[min(len(lengths) - 1, int(p * len(lengths)))]
        print(f"reasoning tokens among closed: min={lengths[0]} p25={pct(.25)} "
              f"median={pct(.5)} p75={pct(.75)} p90={pct(.9)} max={lengths[-1]}")
    print("answers non-empty:", sum(1 for r in rows if r["answer_chars"] > 0),
          "/", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
