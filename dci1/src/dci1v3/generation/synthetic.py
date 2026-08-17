"""The synthetic model adapter (item 63).

Replaces real inference — and nothing else — in the end-to-end lifecycle
test. It reads only what a model would read (the prompt text) and emits
deterministic, seed-controlled responses in the backend's row schema, so the
production cache, storage, selection, masking, and analysis paths run
unchanged over it.

Behaviour: target compliance ~0.65, added-constraint compliance ~0.70,
cap-dependent truncation (0.06 / 0.04 / 0.02) so the pre-screen selects the
smallest registered cap.
"""
from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any

from dci1v3.verifiers.wording_suite import parse_wording

_CONSTRAINT_LINE = re.compile(r"^\d+\.\s+(.*)$")
_FILLER = ("the wind moves north then it turns south over time and the "
           "light shifts while the town wakes to another morning")
_VIOLATION = {"B": "extraordinarily", "RF1": "bold", "RF2": "going",
              "RF3": "o", "RF4": "coffee", "RF5": ",", "RF6": "Q",
              "RF7": "cat", "RF8": "grey"}
_TRUNCATION = {512: 0.06, 768: 0.04, 1024: 0.02}

TARGET_COMPLIANCE = 0.65
ADDED_COMPLIANCE = 0.70


def _parse_constraints(prompt: str) -> list[tuple[str, int]]:
    bound = []
    for line in prompt.split("\n"):
        match = _CONSTRAINT_LINE.match(line.strip())
        if match:
            bound.append(parse_wording(match.group(1)))
    return bound


def _compose(rng: random.Random, target_n: int | None,
             added: tuple[str, int] | None) -> str:
    sentence = "however the wind moves north then it turns south over time."
    if target_n is None:
        count = 1 if rng.random() < 0.05 else 0    # accidental compliance
    elif rng.random() < TARGET_COMPLIANCE:
        count = target_n
    else:
        count = rng.choice([target_n + 1, max(target_n - 1, 0), 0])
    parts = [sentence] * count
    if count == 0:
        parts = [_FILLER + "."]
    if added is not None and rng.random() >= ADDED_COMPLIANCE:
        constraint_id, severity = added
        token = _VIOLATION[constraint_id]
        if constraint_id == "RF5":
            parts.append("," * (severity + 1))
        elif constraint_id == "RF6":
            parts.append("Q" * (severity + 1))
        elif constraint_id == "B":
            parts.append(token)
        else:
            parts.append(" ".join([token] * (severity + 1)))
    return " ".join(parts)


def synthetic_generate(run_dir: Path, plan: dict[str, Any],
                       design_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """GenerateFn-compatible; deterministic per (seed, prompt)."""
    cap = int(plan.get("generation_ceiling", 1024))
    rows = []
    for design in design_rows:
        rng = random.Random(int(design["scientific_seed"]))
        constraints = _parse_constraints(design["user_prompt"])
        target_n = next((sev for cid, sev in constraints if cid == "A"),
                        None)
        added = next(((cid, sev) for cid, sev in constraints if cid != "A"),
                     None)
        text = _compose(rng, target_n, added)
        truncated = rng.random() < _TRUNCATION.get(cap, 0.02)
        if truncated:
            text = text[: max(len(text) - 9, 5)]
        rows.append({
            **design,
            "outcome": "OK",
            "raw_generation": text,
            "final_answer": text,
            "finish_reason": "length" if truncated else "stop",
            "prompt_tokens": len(design["user_prompt"].split()),
            "total_generated_tokens": min(len(text.split()), cap),
            "seed_reasoning": int(design["scientific_seed"]),
        })
    return {"rows": rows,
            "provenance": {"gpu_name": "synthetic",
                           "vllm_version": "synthetic-0",
                           "torch_version": "synthetic-0",
                           "rocm_version": "synthetic-0"}}


def synthetic_judge(run_dir: Path, plan: dict[str, Any],
                    design_rows: list[dict[str, Any]],
                    *, disagree_rate: float = 0.02,
                    invalid_rate: float = 0.0) -> dict[str, Any]:
    """GenerateFn-compatible mocked autorater (A2, tests only).

    Parses the registered judge prompt, answers with the plain reading
    (S0 count vs n), flips the verdict with seeded probability
    ``disagree_rate``, and emits an unparseable output with probability
    ``invalid_rate`` so every status path is exercisable offline.
    """
    from dci1v3.protocol.constants import AUTORATER_PROMPTS
    from dci1v3.verifiers.target import s0_count

    rows = []
    for design in design_rows:
        rng = random.Random(int(design["scientific_seed"]))
        prompt = design["user_prompt"]
        constraint = prompt.split("Rule: ", 1)[1].split("\n", 1)[0]
        body = prompt.split("Text:\n", 1)[1]
        response = body.rsplit("\n---\n", 1)[0]
        n = parse_wording(constraint)[1]
        verdict = s0_count(response) == n
        if rng.random() < disagree_rate:
            verdict = not verdict
        if rng.random() < invalid_rate:
            text = "Maybe; it depends on how one reads the rule."
        else:
            text = ("YES" if verdict else "NO") + \
                "\nCounted the occurrences in the text."
        rows.append({
            **design,
            "outcome": "OK",
            "raw_generation": text,
            "final_answer": text,
            "finish_reason": "stop",
            "prompt_tokens": len(prompt.split()),
            "total_generated_tokens": len(text.split()),
            "seed_reasoning": int(design["scientific_seed"]),
        })
    return {"rows": rows,
            "provenance": {"gpu_name": "synthetic",
                           "vllm_version": "synthetic-0"}}
