"""The generation request/result schema and the explicit failure outcomes.

Stdlib only, on purpose. This module is imported by the plan builders that run
in the SCIENTIFIC environment (torch 2.9.1, no vLLM) as well as by the engine
that runs in the backend environment, so it must never import vllm or torch.

Before this module existed, each backend script invented its own row dict.
`vllm_tp2.py` had three constructors — `build_record`, `unattempted` and the
exception branch — and they did not agree: `unattempted` emitted
`not_generated_reason` and omitted `channel_valid`, so a stopped run produced
rows the ingest could not tell apart from generated ones. One schema, built one
way, removes that class of bug.
"""
from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any


class Outcome(str, enum.Enum):
    """Why a row does or does not carry a behavioural datum.

    These are *results*, not exceptions. A run that cannot execute a checkpoint
    must record the fact and continue, because "this backend could not serve
    this model" is a finding about the software, not a crash.
    """

    #: Generated normally.
    OK = "OK"
    #: The engine cannot serve this checkpoint at all (architecture unknown to
    #: this vLLM build, unsupported dtype/quantisation, missing parser).
    BACKEND_UNSUPPORTED = "BACKEND_UNSUPPORTED"
    #: The checkpoint is supported but does not fit the available VRAM under
    #: the requested envelope. Distinct from UNSUPPORTED: a different envelope
    #: or more cards could succeed.
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
    #: The request was never issued (deadline, chunk abandoned, run stopped).
    #: A missing datum, not a failure and not a zero.
    NOT_GENERATED = "NOT_GENERATED"
    #: Output could not be split into the two channels the condition requires.
    #: Recorded so the cell is not read as "the model answered badly".
    CHANNEL_INVALID = "CHANNEL_INVALID"
    #: Anything else that raised. Carries the exception text.
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"


#: Terminal outcomes that must never be scored as behaviour.
NON_BEHAVIOURAL = frozenset({
    Outcome.BACKEND_UNSUPPORTED, Outcome.CAPACITY_EXCEEDED,
    Outcome.NOT_GENERATED, Outcome.CHANNEL_INVALID, Outcome.TECHNICAL_FAILURE,
})


@dataclass(frozen=True)
class GenerationRequest:
    """One scientific row, rendered-ready. Identity travels with the request.

    `scientific_seed` is a pure function of scientific identity, never of batch
    position: vLLM's scheduler batches and reorders freely, so a seed derived
    from position would make results depend on scheduler order.
    """

    row_id: str
    user_prompt: str
    system_message: str = ""
    scientific_seed: int = 0
    #: Second-phase seed, used only by the two-phase splice strategy.
    answer_seed: int = 0
    #: Opaque scientific identity carried through to the record unchanged.
    identity: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """One generated row. ONE schema, whatever happened.

    Every field is always present. A consumer never has to ask whether a key
    exists, only what its outcome says.
    """

    row_id: str
    outcome: str = Outcome.OK.value
    outcome_detail: str = ""

    rendered_prompt: str = ""
    raw_generation: str = ""
    reasoning_text: str = ""
    final_answer: str = ""

    reasoning_tokens: int = 0
    final_answer_tokens: int = 0
    total_generated_tokens: int = 0

    finish_reason: str = ""
    stop_reason: str = ""

    reasoning_emitted: bool = False
    channel_valid: bool = False
    reasoning_closed: bool = False
    reasoning_cap_hit: bool = False
    answer_truncated: bool = False

    seed_reasoning: int = 0
    seed_answer: int = 0

    identity: dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        """Flatten for JSONL. Identity is merged, never nested, so the stored
        row keeps the shape the existing ingest already reads."""
        row = asdict(self)
        identity = row.pop("identity") or {}
        # Identity first: schema fields win on collision, so a stray identity
        # key can never silently redefine an outcome field.
        return {**identity, **row}

    @property
    def is_behavioural(self) -> bool:
        return Outcome(self.outcome) not in NON_BEHAVIOURAL


#: The exact key set every stored row carries. Used by the schema test.
ROW_KEYS: frozenset[str] = frozenset(
    asdict(GenerationResult(row_id="")).keys()) - {"identity"}


# ------------------------------------------------------- historical artefacts
#: Fields that were RENAMED when this contract became authoritative.
#:
#: `natural_reasoning_closed` and `closed_naturally` were two names for one
#: fact, invented independently by the cross-model and reasoning lines of work.
#: The rest were the reasoning line's shorter names for the same channels.
LEGACY_RENAMES: dict[str, str] = {
    "natural_reasoning_closed": "reasoning_closed",   # cross-model rows
    "closed_naturally": "reasoning_closed",           # reasoning-line rows
    "answer": "final_answer",
    "reasoning": "reasoning_text",
    "answer_tokens": "final_answer_tokens",
}

#: Legacy booleans that are now DERIVED from `outcome`, in this precedence.
#: They were a triple of independent flags whose combinations were not all
#: reachable — `technical_failure and not_generated` had no meaning — which is
#: why the enum replaced them.
_LEGACY_OUTCOME_FLAGS: tuple[tuple[str, str, str], ...] = (
    ("technical_failure", Outcome.TECHNICAL_FAILURE.value,
     "technical_failure_reason"),
    ("not_generated", Outcome.NOT_GENERATED.value, "not_generated_reason"),
)

#: Legacy keys consumed entirely by the derivation above, and never carried
#: forward under their own names.
LEGACY_DERIVED: frozenset[str] = frozenset(
    [flag for flag, _, _ in _LEGACY_OUTCOME_FLAGS]
    + [reason for _, _, reason in _LEGACY_OUTCOME_FLAGS])


def canonicalise_row(row: dict[str, Any]) -> dict[str, Any]:
    """Read a stored row of ANY vintage as the canonical contract.

    This is the ONE migration boundary in the repository, and it exists for a
    single reason: the archived generations are immutable. `raw_generations.jsonl`
    from the pre-consolidation runs carries `natural_reasoning_closed` and the
    boolean triple; the reasoning line's files carry `answer` and `reasoning`.
    Those bytes are the evidence and are not being rewritten.

    It is deliberately NOT a compatibility layer for live code. Nothing writes
    the legacy shape any more, so a consumer calls this once where it loads a
    file and reads canonical names everywhere after. A row that is already
    canonical passes through unchanged, so the call is safe to make
    unconditionally and there is no vintage to detect at the call site.

    `channel_valid` is derived, not defaulted: a legacy row that produced a
    final answer had, by construction, a usable answer channel. A legacy row
    with no answer and no failure flag is left `False`, because the old shape
    could not distinguish "no channel" from "nothing generated" and inventing
    the distinction here would fabricate evidence.
    """
    out = dict(row)

    for legacy, canonical in LEGACY_RENAMES.items():
        if legacy in out:
            value = out.pop(legacy)
            out.setdefault(canonical, value)

    if "outcome" not in out:
        outcome, detail = Outcome.OK.value, ""
        for flag, mapped, reason_key in _LEGACY_OUTCOME_FLAGS:
            if out.get(flag):
                outcome, detail = mapped, str(out.get(reason_key) or "")
                break
        out["outcome"] = outcome
        out.setdefault("outcome_detail", detail)
    for key in LEGACY_DERIVED:
        out.pop(key, None)

    if "channel_valid" not in out:
        out["channel_valid"] = bool(
            out.get("final_answer") and out["outcome"] == Outcome.OK.value)

    for key, default in (("reasoning_closed", False), ("seed_answer", 0),
                         ("stop_reason", ""), ("outcome_detail", "")):
        out.setdefault(key, default)
    return out
