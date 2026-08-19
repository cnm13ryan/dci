"""Judgment parsing for the diagnostic runs.

The vLLM OpenAI server splits the harmony transcript for us: the
response message carries the analysis channel in ``reasoning`` /
``reasoning_content`` and the final channel in ``content``. This parser
therefore reads only the FINAL content; reasoning is retained as a
separate diagnostic observable, never merged into the verdict. The
vocabulary and prefix rules mirror the registered parser
(gate1-parse/2.0.0): SATISFIES -> pass, VIOLATES -> fail; everything
else keeps a distinct operational status and is never recoded."""

VALID = "valid"
INVALID_OUTPUT = "invalid_output"
REFUSAL = "refusal"
GENERATION_FAILURE = "generation_failure"

LABEL_MAPPING = {"SATISFIES": "pass", "VIOLATES": "fail"}

_REFUSAL_MARKERS = (
    "i cannot", "i can't", "i won't", "i will not", "as an ai",
    "i'm sorry", "i am sorry", "cannot help", "can't help",
    "cannot assist", "can't assist", "unable to help",
)


def parse_final(content: str | None) -> tuple[str, str | None,
                                              str | None]:
    """(status, label, justification) from the FINAL channel only."""
    text = (content or "").strip()
    if not text:
        return INVALID_OUTPUT, None, None
    first, _, rest = text.partition("\n")
    token = "".join(ch for ch in first.strip().upper() if ch.isalpha())
    if token.startswith("SATISF"):
        return VALID, LABEL_MAPPING["SATISFIES"], rest.strip() or None
    if token.startswith("VIOLAT"):
        return VALID, LABEL_MAPPING["VIOLATES"], rest.strip() or None
    lowered = text.lower()
    if any(marker in lowered for marker in _REFUSAL_MARKERS):
        return REFUSAL, None, None
    return INVALID_OUTPUT, None, None
