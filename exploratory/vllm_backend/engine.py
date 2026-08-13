"""THE canonical vLLM engine. The only `LLM(...)` construction in the repository.

`tests/test_single_engine_site.py` fails the build if `LLM(` appears in any other
module, which is what stops the eight-call-site situation from reforming.

Two generation strategies live here, and they are NOT interchangeable — they are
different experimental conditions:

* `single_phase` — ONE uninterrupted generation. No stop string, no splice, no
  forced close. Reasoning and answer share the budget and the model closes its
  own reasoning. A request that reaches the ceiling stops there and is recorded
  with `reasoning_cap_hit`. Nothing closes a trace on the model's behalf.

* `two_phase_splice` — phase 1 thinks under an assigned budget and is stopped at
  the close delimiter; phase 2 answers under a budget identical in every
  treatment. Used by the reasoning-budget grid, where the point is to VARY the
  thinking budget, which one uninterrupted generation cannot do.

The earlier two-phase splice produced a documented artefact on some checkpoints
(the model kept thinking into the answer phase and re-answered), which is why
the cross-model runs use `single_phase`. Both are kept because both have been
executed and their outputs are on disk.
"""
from __future__ import annotations

import time
from typing import Any

from vllm_backend import records
from vllm_backend.contract import GenerationRequest, GenerationResult, Outcome
from vllm_backend.plan import EnginePlan, RunPlan, SamplingPlan
from vllm_backend.registry import ModelCard


class TemplateSwitchError(RuntimeError):
    """A declared chat-template switch had no effect on the rendered prompt.

    Jinja silently ignores unknown kwargs, so a renamed or absent switch yields
    no error and the WRONG experimental condition. Turning that into a loud
    failure is the single highest-value check in this package.
    """


def build_engine(plan: EnginePlan):
    """Construct the vLLM engine. THE ONLY `LLM(...)` CALL IN THE REPOSITORY.

    Returns `(llm, tokenizer, load_seconds)`.
    """
    from vllm import LLM

    started = time.perf_counter()
    llm = LLM(**plan.engine_kwargs())          # noqa: VLLM001 - canonical site
    load_seconds = time.perf_counter() - started
    return llm, llm.get_tokenizer(), load_seconds


def build_sampling(sampling: SamplingPlan, max_tokens: int, seed: int):
    """One `SamplingParams` construction path."""
    from vllm import SamplingParams

    kwargs: dict[str, Any] = {
        "temperature": sampling.temperature,
        "top_p": sampling.top_p,
        # vLLM disables top-k with <= 0; the canonical run leaves it off.
        "top_k": sampling.top_k if sampling.top_k and sampling.top_k > 0 else -1,
        "max_tokens": int(max_tokens),
        "seed": int(seed),
    }
    if sampling.stop:
        kwargs["stop"] = list(sampling.stop)
        kwargs["include_stop_str_in_output"] = sampling.include_stop_str_in_output
    return SamplingParams(**kwargs)


def render_prompt(tokenizer, request: GenerationRequest,
                  template_kwargs: dict[str, Any]) -> str:
    """Apply the chat template. System turn included only when present."""
    messages = []
    if request.system_message:
        messages.append({"role": "system", "content": request.system_message})
    messages.append({"role": "user", "content": request.user_prompt})
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, **template_kwargs)


def verify_template_switch(tokenizer, request: GenerationRequest,
                           template_kwargs: dict[str, Any]) -> dict[str, Any]:
    """Prove a declared boolean switch actually changes the rendered prompt.

    Renders the same messages with the switch as declared and with it negated.
    If the two strings are identical the kwarg is inert — the template has no
    such variable, or it was renamed upstream — and the run would silently
    execute the wrong reasoning condition. That is refused here.
    """
    evidence: dict[str, Any] = {"checked": [], "kwargs": dict(template_kwargs)}
    for key, value in template_kwargs.items():
        if not isinstance(value, bool):
            continue
        as_declared = render_prompt(tokenizer, request, template_kwargs)
        negated = render_prompt(tokenizer, request,
                                {**template_kwargs, key: not value})
        if as_declared == negated:
            raise TemplateSwitchError(
                f"chat template kwarg {key}={value!r} does not change the "
                f"rendered prompt — the template ignores it, so the reasoning "
                f"condition would be whatever the template defaults to. "
                f"Refusing to run rather than record a wrong condition.")
        evidence["checked"].append({
            "kwarg": key, "declared": value, "template_differs": True,
            "declared_tail": as_declared[-120:], "negated_tail": negated[-120:],
        })
    return evidence


def generate_single_phase(llm, tokenizer, requests: list[GenerationRequest],
                          prompts: list[str], sampling: SamplingPlan,
                          parser, card: ModelCard) -> list[GenerationResult]:
    """ONE uninterrupted generation per request; the model closes its own trace."""
    from vllm_backend.reasoning import split

    params = [build_sampling(sampling, sampling.max_tokens, r.scientific_seed)
              for r in requests]
    outputs = llm.generate(prompts, params)

    results = []
    for request, prompt, output in zip(requests, prompts, outputs):
        try:
            completion = output.outputs[0]
            reasoning, answer = split(parser, completion.text,
                                      card.think_open, card.think_close)
            results.append(records.generated(
                request, prompt, completion, reasoning, answer,
                card.think_close, tokenizer))
        except Exception as error:
            results.append(records.failed(request, prompt, error))
    return results


def generate_two_phase_splice(llm, tokenizer, requests: list[GenerationRequest],
                              prompts: list[str], sampling: SamplingPlan,
                              parser, card: ModelCard) -> list[GenerationResult]:
    """Phase 1 thinks under the assigned budget; phase 2 answers under a fixed one.

    The reasoning channel is never part of the response: phase 2 is a separate
    generation whose prompt is `prompt + reasoning + close_delimiter`, and only
    its output becomes the answer.
    """
    close = card.think_close
    think_sampling = SamplingPlan(
        temperature=sampling.temperature, top_p=sampling.top_p,
        top_k=sampling.top_k, max_tokens=sampling.max_tokens,
        answer_tokens=sampling.answer_tokens,
        stop=(close,), include_stop_str_in_output=False)

    think_params = [build_sampling(think_sampling, think_sampling.max_tokens,
                                   r.scientific_seed) for r in requests]
    thoughts = llm.generate(prompts, think_params)

    continued, meta = [], []
    for prompt, output in zip(prompts, thoughts):
        completion = output.outputs[0]
        closed = completion.finish_reason == "stop"
        continued.append(f"{prompt}{completion.text}{close}\n\n")
        meta.append((completion.text, len(completion.token_ids), closed))

    answer_params = [build_sampling(sampling, sampling.answer_tokens,
                                    r.answer_seed or r.scientific_seed + 1)
                     for r in requests]
    answers = llm.generate(continued, answer_params)

    results = []
    for request, prompt, (text, n_tokens, closed), output in zip(
            requests, prompts, meta, answers):
        try:
            results.append(records.spliced(
                request, prompt, text, n_tokens, closed,
                output.outputs[0], tokenizer))
        except Exception as error:
            results.append(records.failed(request, prompt, error))
    return results


STRATEGIES = {
    "single_phase": generate_single_phase,
    "two_phase_splice": generate_two_phase_splice,
}


def run(engine_plan: EnginePlan, sampling: SamplingPlan, run_plan: RunPlan,
        card: ModelCard, requests: list[GenerationRequest],
        on_chunk=None, verify_switch: bool = True) -> dict[str, Any]:
    """Execute a whole run: preflight, engine, chunked generation, provenance.

    `on_chunk(results)` is called as each chunk completes so a stopped run still
    leaves every finished row on disk.
    """
    from vllm_backend import capabilities, hardware
    from vllm_backend.reasoning import NullParser, build_parser

    host = hardware.probe()
    capability = None
    try:
        capability = capabilities.probe(
            engine_plan.model_id, engine_plan.model_revision,
            engine_plan.trust_remote_code, card.reasoning_parser)
    except Exception:
        pass

    ok, outcome, detail = capabilities.preflight(
        card, engine_plan, host, capability)
    if not ok:
        blocked = records.blocked(requests, outcome, detail)
        if on_chunk:
            on_chunk(blocked)
        return {"results": blocked, "provenance": {
            "blocked": True, "outcome": outcome, "detail": detail,
            "host": host.to_dict(), "capability": capability,
            "engine_kwargs": {k: str(v) for k, v in
                              engine_plan.engine_kwargs().items()}}}

    memory_before = hardware.rocm_smi_memory()
    try:
        llm, tokenizer, load_seconds = build_engine(engine_plan)
    except Exception as error:
        # Weight load is where a too-large checkpoint fails. That is capacity,
        # not an unsupported architecture, and the distinction matters.
        text = f"{type(error).__name__}: {error}"
        capacity = any(s in text.lower() for s in
                       ("out of memory", "oom", "no available memory",
                        "not enough memory", "free memory"))
        blocked = records.blocked(
            requests,
            Outcome.CAPACITY_EXCEEDED.value if capacity
            else Outcome.TECHNICAL_FAILURE.value, text[:500])
        if on_chunk:
            on_chunk(blocked)
        return {"results": blocked, "provenance": {
            "blocked": True, "engine_error": text[:2000],
            "host": host.to_dict(), "capability": capability,
            "engine_kwargs": {k: str(v) for k, v in
                              engine_plan.engine_kwargs().items()}}}
    memory_after = hardware.rocm_smi_memory()

    # A NO_THINKING run has no reasoning channel to split out.
    if run_plan.reasoning_mode == "NO_THINKING":
        parser, parser_label = NullParser(), "none (NO_THINKING: no channel)"
    else:
        parser, parser_label = build_parser(
            card.reasoning_parser, tokenizer, card.think_open, card.think_close)

    template_kwargs = dict(run_plan.chat_template_kwargs)
    switch_evidence: dict[str, Any] = {}
    if requests and verify_switch and template_kwargs:
        switch_evidence = verify_template_switch(
            tokenizer, requests[0], template_kwargs)

    prompts = [render_prompt(tokenizer, r, template_kwargs) for r in requests]

    strategy = STRATEGIES[run_plan.strategy]
    chunk_size = max(1, int(run_plan.chunk_size or len(requests) or 1))
    deadline = run_plan.deadline_seconds
    started = time.perf_counter()

    results: list[GenerationResult] = []
    for start in range(0, len(requests), chunk_size):
        window = slice(start, min(start + chunk_size, len(requests)))
        spent = time.perf_counter() - started
        if deadline and spent > float(deadline):
            why = (f"whole-run deadline {deadline}s exceeded after "
                   f"{spent:.0f}s and {len(results)} rows")
            chunk = [records.not_generated(r, p, why)
                     for r, p in zip(requests[window], prompts[window])]
        else:
            chunk = strategy(llm, tokenizer, requests[window], prompts[window],
                             sampling, parser, card)
        results.extend(chunk)
        if on_chunk:
            on_chunk(chunk)

    elapsed = time.perf_counter() - started
    provenance = {
        "blocked": False,
        "engine_kwargs": {k: str(v) for k, v in
                          engine_plan.engine_kwargs().items()},
        "sampling": sampling.to_dict(),
        "run": run_plan.to_dict(),
        "model_card": {
            "model_id": card.model_id, "family": card.family,
            "reasoning_parser": card.reasoning_parser,
            "think_open": card.think_open, "think_close": card.think_close,
            "supported_modes": list(card.supported_modes),
        },
        "reasoning_parser_used": parser_label,
        "template_switch_evidence": switch_evidence,
        "preflight_detail": detail,
        "host": host.to_dict(),
        "capability": capability,
        "load_seconds": round(load_seconds, 1),
        "generation_seconds": round(elapsed, 1),
        "rocm_smi_before_load": memory_before,
        "rocm_smi_after_load": memory_after,
        "torch_memory_this_process": hardware.torch_memory(),
        "rendered_prompt_example": prompts[0][-400:] if prompts else "",
        "summary": records.summarise(results),
    }
    return {"results": results, "provenance": provenance}
