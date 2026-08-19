"""Inspect Scout scanners over the forensics eval logs.

Add scanners HERE after manual inspection reveals a recurring
phenomenon; run them with `scans/run_scan.py` (or `scout scan`).
Scout results land in `scans/results/` — never inside the immutable
raw Inspect logs and never inside registered DCI evidence.

The example scanner is deliberately simple and deterministic: it flags
transcripts whose reasoning (analysis channel) last concludes one
verdict while the final message emits the other — the
verdict/justification-contradiction phenomenon observed once in the
registered development rounds.
"""

import re

from inspect_ai.model import ChatMessage, ChatMessageAssistant
from inspect_scout import Result, scanner


def _assistant_parts(messages: list) -> "tuple[str, str]":
    """(reasoning_text, final_text) from the last assistant message."""
    reasoning, final = [], []
    for message in messages or []:
        if not isinstance(message, ChatMessageAssistant):
            continue
        content = message.content
        if isinstance(content, str):
            final = [content]
            reasoning = []
            continue
        reasoning, final = [], []
        for part in content:
            kind = getattr(part, "type", None)
            if kind == "reasoning":
                reasoning.append(part.reasoning)
            elif kind == "text":
                final.append(part.text)
    return "\n".join(reasoning), "\n".join(final)


def _final_label(final_text: str) -> "str | None":
    first = final_text.strip().splitlines()[0] if final_text.strip() \
        else ""
    token = "".join(ch for ch in first.upper() if ch.isalpha())
    if token.startswith("SATISF"):
        return "SATISFIES"
    if token.startswith("VIOLAT"):
        return "VIOLATES"
    return None


def _reasoning_verdict(reasoning: str) -> "str | None":
    """The label the reasoning decides on: its LAST uppercase quoted
    verdict token. A lowercase-phrase variant was refuted by manual
    inspection (gpt-oss's format meta-commentary 'That satisfies.'
    refers to the output format, not the rule)."""
    # Quoted alternatives in format reminders ('"SATISFIES" or
    # "VIOLATES"') are not decisions; strip them first (second
    # refinement from manual inspection).
    cleaned = re.sub(r"(?:\"|')?SATISFIES(?:\"|')?\s+or\s+(?:\"|')?VIOLATES(?:\"|')?", " ",
                     reasoning or "")
    hits = re.findall(r"\b(SATISFIES|VIOLATES)\b", cleaned)
    return hits[-1] if hits else None


@scanner(messages="all")
def reasoning_final_contradiction():
    """Reasoning concludes one verdict; the final answer emits the
    other."""
    async def scan(messages: list[ChatMessage]) -> Result:
        reasoning, final = _assistant_parts(messages)
        final_label = _final_label(final)
        implied = _reasoning_verdict(reasoning)
        hit = (final_label is not None and implied is not None
               and final_label != implied)
        return Result(
            value=hit,
            answer=final_label,
            explanation=(f"reasoning implies {implied}, final says "
                         f"{final_label}" if hit else None),
            metadata={"implied_by_reasoning": implied,
                      "final_label": final_label,
                      "reasoning_chars": len(reasoning)})
    return scan
