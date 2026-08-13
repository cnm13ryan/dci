"""Ask vLLM what it supports, instead of hard-coding a support list.

This is the module that replaces name-string branching with upstream truth. It
runs in the backend environment and answers, for the LIVE wheel:

  * is this checkpoint's architecture registered at all?
  * is it multimodal?
  * does it need remote code?
  * which reasoning parsers exist?

The support matrix genuinely differs between builds — vLLM 0.15.1 registers
neither `Qwen3_5*` nor `Gemma4*` architectures and has no `gemma4` reasoning
parser, while 0.27.1 has all three — so a hard-coded list would be wrong for one
of them. Asking the wheel is the only thing that stays correct across both.
"""
from __future__ import annotations

from typing import Any


def probe(model_id: str, revision: str = "", trust_remote_code: bool = False,
          reasoning_parser: str | None = None) -> dict[str, Any]:
    """Everything the installed wheel can tell us about this checkpoint.

    Every field is TRISTATE: True, False, or None for "could not be
    determined". That distinction is the whole safety property — an earlier
    version of this probe returned False when the vLLM API had merely moved,
    and `preflight` then blocked a perfectly runnable checkpoint as
    BACKEND_UNSUPPORTED. Only a definite negative may block a run.
    """
    result: dict[str, Any] = {
        "model_id": model_id,
        "architectures": [],
        "vllm_supported": None,
        "is_multimodal": None,
        "needs_remote_code": None,
        "reasoning_parser_available": None,
        "probe_error": "",
    }
    if reasoning_parser:
        from vllm_backend.reasoning import parser_available

        result["reasoning_parser_available"] = parser_available(reasoning_parser)

    try:
        from transformers import AutoConfig

        kwargs: dict[str, Any] = {"trust_remote_code": trust_remote_code}
        if revision:
            kwargs["revision"] = revision
        config = AutoConfig.from_pretrained(model_id, **kwargs)
        architectures = list(getattr(config, "architectures", None) or [])
        result["architectures"] = architectures
        result["needs_remote_code"] = bool(getattr(config, "auto_map", None))
    except Exception as error:
        result["probe_error"] = f"config: {type(error).__name__}: {error}"[:400]
        return result

    try:
        from vllm.model_executor.models import ModelRegistry

        # `get_supported_archs()` is the stable accessor across the builds on
        # this host (verified: 272 architectures on 0.15.1, 367 on 0.27.1).
        # `is_text_generation_model` is NOT usable here — on 0.15.1 it requires
        # a fully built `ModelConfig`, which needs the weights we are trying to
        # decide whether to load.
        known = set(ModelRegistry.get_supported_archs())
        supported = [a for a in architectures if a in known]
        result["supported_architectures"] = supported
        # Only claim False when the registry answered AND the checkpoint
        # declared architectures; an empty `architectures` list means the
        # config told us nothing, not that the model is unsupported.
        result["vllm_supported"] = bool(supported) if architectures else None
        if supported:
            try:
                info = ModelRegistry.inspect_model_cls(supported[0])
                # vLLM has moved this attribute around between releases; treat
                # its absence as unknown rather than as False.
                for attribute in ("supports_multimodal", "is_multimodal"):
                    if hasattr(info, attribute):
                        result["is_multimodal"] = bool(getattr(info, attribute))
                        break
            except Exception:
                pass
    except Exception as error:
        result["probe_error"] = f"registry: {type(error).__name__}: {error}"[:400]

    return result


def preflight(card, plan, host, capability: dict[str, Any] | None = None
              ) -> tuple[bool, str, str]:
    """Gate a run before any weight is read.

    Returns `(ok, outcome, detail)`. A block is a RESULT — the caller writes one
    row per design row with that outcome — never an exception, because "this
    build cannot serve this checkpoint" is a finding about the software.
    """
    from vllm_backend.contract import Outcome

    if capability is None:
        return True, Outcome.OK.value, "no capability probe available"

    if capability.get("vllm_supported") is False:
        return (False, Outcome.BACKEND_UNSUPPORTED.value,
                f"{card.model_id} declares architectures "
                f"{capability.get('architectures')}; this vLLM build "
                f"({host.vllm_version or 'unknown'}) registers none of them")

    if capability.get("reasoning_parser_available") is False:
        # Not fatal: `reasoning.build_parser` falls back to the card's
        # delimiters and labels the row accordingly. Surfaced so the run record
        # says the fallback happened.
        return (True, Outcome.OK.value,
                f"card names reasoning parser {card.reasoning_parser!r}, which "
                f"this build does not register; falling back to the "
                f"checkpoint's documented delimiters")

    if plan.tensor_parallel_size > max(host.device_count, 1):
        return (False, Outcome.CAPACITY_EXCEEDED.value,
                f"tensor_parallel_size={plan.tensor_parallel_size} exceeds the "
                f"{host.device_count} visible device(s)")

    return True, Outcome.OK.value, ""
