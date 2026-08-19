"""A deterministic synthetic generator for CPU-only tests (§T14 of the brief).

It substitutes real inference at exactly one seam — the ``GenerateFn`` the
cache calls — so every other line of the production path runs unchanged in
tests: the same plan, the same design rows, the same row schema, the same
provenance, the same integrity checks.

The text it produces is a function of the scientific seed alone, so a run is
reproducible, and it is deliberately varied enough to exercise the whole
compliance vector: passes and failures on each constraint form, empty answers,
short answers below the non-vacuity threshold, and truncated answers.

Nothing here is scientific. Synthetic rows can only ever be written into a
synthetic-namespace context (engine/context.py refuses the mix).
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

SENTENCES = (
    "the river runs west then it drifts to the north",
    "people often notice the change before they can explain it",
    "one useful way to see this is to start from the ordinary case",
    "a bright bold banner was going up by the bay",
    "coffee, tea, and a little sugar, in that order, every morning",
    "MANY READERS FIND THIS SORT OF THING HARD TO FOLLOW",
    "extraordinarily complicated arrangements rarely survive contact",
)


def synthetic_text(seed: int) -> tuple[str, str, int]:
    """Return (text, finish_reason, generated_tokens) for one scientific seed."""
    rng = random.Random(seed)
    shape = rng.random()
    if shape < 0.03:
        return "", "stop", 0
    if shape < 0.08:
        return "Yes.", "stop", 2
    however = rng.randint(0, 5)
    body = [rng.choice(SENTENCES) for _ in range(rng.randint(2, 6))]
    for _ in range(however):
        body.insert(rng.randrange(len(body) + 1), "however")
    text = ". ".join(body) + "."
    if rng.random() < 0.07:
        return text[: max(8, len(text) // 2)], "length", 512
    return text, "stop", max(1, len(text) // 4)


def synthetic_generate(run_dir: Path, plan: dict[str, Any],
                       design_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """A ``GenerateFn`` that never touches a GPU."""
    rows = []
    for request in design_rows:
        seed = int(request["scientific_seed"])
        text, finish_reason, tokens = synthetic_text(seed)
        rows.append({
            "row_id": request["row_id"], "outcome": "OK",
            "final_answer": text, "raw_generation": text,
            "finish_reason": finish_reason, "total_generated_tokens": tokens,
            "prompt_tokens": len(request["user_prompt"].split()),
            "scientific_seed": seed, "seed_reasoning": seed,
        })
    return {"rows": rows,
            "provenance": {"backend": "synthetic", "vllm_version": "synthetic",
                           "gpu_name": "none",
                           "model_id": plan.get("model_id"),
                           "revision": plan.get("revision")}}
