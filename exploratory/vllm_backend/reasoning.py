"""Reasoning-channel splitting: vLLM's registered parser, or the card's delimiters.

Migrated verbatim in semantics from `crossmodel/vllm_tp2.py`, which was the only
one of the eight backend scripts that got this right. The others split on a
hard-coded `</think>`, which silently mis-parses Gemma 4 (channel markers) and
Kimi-VL (`◁think▷`).

vLLM is imported lazily so the module stays importable without a GPU stack.
"""
from __future__ import annotations


class DelimiterParser:
    """Fallback splitter for a checkpoint vLLM registers no parser for.

    Used for Kimi-VL-A3B-Thinking-2506, whose model card ships the reference
    implementation:

        extract_thinking_and_summary(text, bot="◁think▷", eot="◁/think▷")

    with one deliberate difference. Where the card returns the whole text as the
    summary when no marker is present, this returns an EMPTY answer, because a
    scored scratchpad is worse than a missing datum. Content emitted BEFORE the
    opening marker is treated as answer, so the split does not assume an
    ordering the template does not enforce.
    """

    def __init__(self, start: str, end: str):
        self.start, self.end = start, end

    def extract_reasoning(self, text: str, request=None):
        if self.end in text:
            head, _, tail = text.partition(self.end)
            if self.start in head:
                leading, _, reasoning = head.partition(self.start)
            else:
                leading, reasoning = "", head
            answer = f"{leading.strip()}\n{tail.strip()}".strip()
            return reasoning.strip("\n"), answer
        if self.start in text:
            return text.split(self.start, 1)[1].strip("\n"), ""
        # Markerless output in a thinking condition. Returning the raw text
        # would hand the whole generation to the behavioural verifiers as if it
        # were a final answer; in an always-thinking checkpoint whose parser has
        # failed, that text is a scratchpad, and scoring a scratchpad
        # manufactures a behavioural datum out of a parser failure.
        #
        # The raw generation is preserved by the caller under `raw_generation`,
        # so nothing is lost for diagnosis; what is refused is the promotion of
        # unsegmented text to a final answer.
        return None, ""


class NullParser:
    """The splitter for a NO_THINKING condition: there is no reasoning channel.

    In a thinking condition, markerless output means the parser failed and the
    text is an unsegmented scratchpad, so `DelimiterParser` refuses to promote
    it to an answer. In a NON-thinking condition the opposite is true: no
    delimiter is EXPECTED, and the whole generation is the answer. Applying the
    delimiter parser there marks every row CHANNEL_INVALID and throws away a
    perfectly valid run — which is exactly what happened the first time this
    backend was exercised end to end on a non-reasoning checkpoint.
    """

    def extract_reasoning(self, text: str, request=None):
        return "", (text or "").strip()


def parser_available(name: str) -> bool | None:
    """Does this build register `name`? `None` when the question cannot be asked.

    `ReasoningParserManager.reasoning_parsers` is populated LAZILY — it is an
    empty dict until something looks a parser up — so enumerating it answers
    "which parsers have been used so far", not "which exist". Verified on both
    0.15.1 and 0.27.1: the dict holds 0 entries at import and 1 after a single
    `get_reasoning_parser("qwen3")`. The only honest probe is to ask for the
    specific name.

    Returns None rather than False when vLLM is absent or the API has moved, so
    an unanswerable question is never mistaken for a negative answer.
    """
    try:
        from vllm.reasoning import ReasoningParserManager
    except Exception:
        return None
    try:
        ReasoningParserManager.get_reasoning_parser(name)
        return True
    except KeyError:
        return False
    except Exception:
        # Some builds raise a bespoke error for an unknown name; treat a
        # non-KeyError as "cannot tell" rather than a definite absence.
        return None


def build_parser(name: str | None, tokenizer, start: str, end: str):
    """vLLM's registered parser when there is one, the delimiters otherwise.

    Returns `(parser, label)`. The label is recorded with the run so a stored
    row always says which splitter produced it.
    """
    if not name:
        return DelimiterParser(start, end), f"delimiters({start} … {end})"
    from vllm.reasoning import ReasoningParserManager

    try:
        cls = ReasoningParserManager.get_reasoning_parser(name)
    except Exception as error:
        # A card naming a parser this build does not register is a real
        # mismatch, but it must not lose the run: fall back to the documented
        # delimiters and say so in the label.
        return (DelimiterParser(start, end),
                f"delimiters({start} … {end}) [vllm has no {name!r}: {error}]")
    return cls(tokenizer), f"vllm:{name}"


def split(parser, text: str, think_open: str = "",
          think_close: str = "") -> tuple[str, str]:
    """`(reasoning, answer)`, never raising, never returning raw text as both.

    When the delimiters are supplied, a failed split is REPAIRED rather than
    recorded. This matters for templates that **pre-open** the reasoning block:
    Qwen3-Thinking renders `...<|im_start|>assistant\n<think>\n`, so the opening
    marker is in the PROMPT and never appears in the generation. vLLM's `qwen3`
    parser looks for that opening marker in the output, does not find it, and
    returns the whole trace as content — leaking the entire reasoning channel
    into the scored answer, silently and with `outcome == OK`.

    Verified on this host with vLLM 0.15.1 and Qwen3-4B-Thinking-2507: all four
    probe rows contained `</think>` and no `<think>`, and the parser assigned
    100% of the reasoning text to the answer. `DelimiterParser` gets this case
    right, so it is used as the repair.

    The repair fires only when the parser found NO reasoning while a close
    delimiter is present — i.e. only when the split provably failed.
    """
    try:
        reasoning, content = parser.extract_reasoning(text, None)
    except Exception:
        try:
            reasoning, content = parser.extract_reasoning(text)
        except Exception:
            return "", ""
    reasoning = (reasoning or "").strip("\n")
    content = (content or "").strip()

    if not reasoning and think_close and think_close in (text or ""):
        repaired_reasoning, repaired_answer = DelimiterParser(
            think_open, think_close).extract_reasoning(text)
        if repaired_reasoning:
            return repaired_reasoning.strip("\n"), (repaired_answer or "").strip()
    return reasoning, content
