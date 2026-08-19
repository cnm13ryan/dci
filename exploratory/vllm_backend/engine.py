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
    tokenizer = llm.get_tokenizer()
    # STAMPED, like `load_tokenizer` stamps the one it fetches. This is the
    # engine's own tokenizer -- the strongest provenance there is, because it
    # is literally the object generation will use -- and without the stamp the
    # switch evidence recorded "unknown" for it, which is what the retained
    # hardware-validation artifact then claimed about every executed case.
    tokenizer._dci_acquisition = ACQUIRED_FROM_ENGINE
    tokenizer._dci_revision = plan.model_revision
    return llm, tokenizer, load_seconds


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
        "skip_special_tokens": sampling.skip_special_tokens,
    }
    if sampling.stop:
        kwargs["stop"] = list(sampling.stop)
        kwargs["include_stop_str_in_output"] = sampling.include_stop_str_in_output
    return SamplingParams(**kwargs)


# How a tokenizer was obtained, recorded on it and carried into the switch
# evidence. Named constants rather than literals repeated at the assertion site:
# a test that sniffed for the substring "vllm" matched the FALLBACK string too,
# because that string says "(vllm util absent)". The guard meant to skip then
# fired the assertion instead, and the suite failed in the one environment the
# test exists to cover.

#: The engine's OWN tokenizer, from a constructed `LLM`. The strongest of the
#: three: it is the object that renders the prompts, so no second acquisition
#: can disagree with it. `build_engine` stamps this.
ACQUIRED_FROM_ENGINE = "vllm.LLM.get_tokenizer"
#: `load_tokenizer`'s preferred path, for validating before paying a weight load.
ACQUIRED_BY_VLLM = "vllm.transformers_utils.get_tokenizer"
#: Same, where the wheel has moved the utility. Recorded so a template certified
#: through it is never mistaken for one certified through the engine's path.
ACQUIRED_BY_FALLBACK = "transformers.AutoTokenizer (vllm util absent)"


def vllm_tokenizer_utility_available() -> bool:
    """Whether this interpreter has the utility `load_tokenizer` prefers.

    The wheels move it: it is `vllm.transformers_utils.tokenizer.get_tokenizer`
    on the 0.15 line the study pins, and absent under 0.27. Which branch runs is
    a property of the environment, so a test asserts the branch it is actually
    in rather than assuming either.
    """
    try:
        from vllm.transformers_utils.tokenizer import get_tokenizer  # noqa: F401
    except Exception:                                   # noqa: BLE001
        return False
    return True


def load_tokenizer(card: ModelCard, revision: str = ""):
    """THE tokenizer, acquired the way inference acquires it.

    `build_engine` returns `llm.get_tokenizer()`, which is authoritative but
    costs a full weight load. Chat-template behaviour needs checking BEFORE that
    -- a wrong reasoning condition should be refused in seconds, not after eight
    gigabytes have been read -- so this exists to answer the same question at
    the same source without the engine.

    `revision` must be the SAME pin the run passes to `LLM(...)` via
    `EnginePlan.model_revision`. A tokenizer resolved at `main` while inference
    pins a commit is a second path wearing the first one's name -- the chat
    template could differ between them, which is the whole failure this function
    exists to prevent.

    It goes through vLLM's own tokenizer utility rather than
    `transformers.AutoTokenizer`. That distinction is the point: a second
    acquisition path could resolve a different revision, a different
    `trust_remote_code` decision or a different chat template from the one
    inference will use, and then validation would be certifying a template the
    run never renders.
    """
    try:
        from vllm.transformers_utils.tokenizer import get_tokenizer
    except Exception:                                   # noqa: BLE001
        # Older/newer wheels move this. Fall back, and SAY SO on the record, so
        # a template certified through the fallback is not mistaken for one
        # certified through the engine's own path.
        import transformers
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            card.model_id, revision=revision or None,
            trust_remote_code=card.trust_remote_code)
        tokenizer._dci_acquisition = ACQUIRED_BY_FALLBACK
        tokenizer._dci_revision = revision
        return tokenizer
    tokenizer = get_tokenizer(card.model_id, revision=revision or None,
                              trust_remote_code=card.trust_remote_code)
    tokenizer._dci_acquisition = ACQUIRED_BY_VLLM
    tokenizer._dci_revision = revision
    return tokenizer


def validate_reasoning_control(card: ModelCard, tokenizer,
                               request: GenerationRequest) -> dict[str, Any]:
    """Prove the card's reasoning declarations are true of the real template.

    `verify_template_switch` checks the ONE mode a run is about to execute.
    This checks every mode the card claims to support, which is what makes the
    card itself evidence rather than an assertion: a checkpoint that declares
    four modes and whose template implements one is a registry error, and it is
    cheaper to find here than in the analysis of a finished run.

    Also asserts that modes declaring DIFFERENT template kwargs actually render
    differently. A card can pass every per-mode switch check and still collapse
    two conditions into one prompt, and no per-mode check can see that.

    Modes that declare the SAME kwargs are expected to render the same, and
    that is not a fault: LIMITED_REASONING, NATURAL_REASONING and
    THINKING_ENABLED_BOUNDED all render with thinking enabled and differ in
    their BUDGET policy -- capped think phase, uncapped, and a generation
    ceiling respectively. The prompt is the same by design; the sampling plan is
    what separates them.
    """
    evidence: dict[str, Any] = {
        "model_id": card.model_id,
        "tokenizer_acquisition": getattr(tokenizer, "_dci_acquisition", "unknown"),
        "tokenizer_revision": getattr(tokenizer, "_dci_revision", ""),
        "supported_modes": list(card.supported_modes),
        "modes": {},
    }
    rendered: dict[str, str] = {}
    declared: dict[str, dict[str, Any]] = {}
    for mode in card.supported_modes:
        kwargs = card.template_kwargs(mode)
        declared[mode] = kwargs
        evidence["modes"][mode] = verify_template_switch(
            tokenizer, request, kwargs, card, mode)
        rendered[mode] = render_prompt(tokenizer, request, kwargs)

    modes = list(rendered)
    collisions = [
        (a, b) for i, a in enumerate(modes) for b in modes[i + 1:]
        if declared[a] != declared[b] and rendered[a] == rendered[b]]
    if collisions:
        raise TemplateSwitchError(
            f"{card.model_id} declares different template kwargs for "
            f"{collisions} and yet they render IDENTICALLY. Two experimental "
            f"conditions sharing one prompt is not a condition, it is a "
            f"mislabel — the template does not implement the distinction the "
            f"card claims.")
    evidence["modes_render_distinctly"] = True
    # Which modes share a prompt BY DESIGN, so a reader can see that the three
    # thinking budgets are separated by sampling rather than by rendering.
    evidence["modes_sharing_a_prompt"] = sorted(
        {tuple(sorted((a, b))) for i, a in enumerate(modes) for b in modes[i + 1:]
         if rendered[a] == rendered[b]})
    evidence["pre_opens_reasoning"] = {
        mode: text.rstrip().endswith(card.think_open)
        for mode, text in rendered.items()} if card.think_open else {}
    return evidence


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
                           template_kwargs: dict[str, Any],
                           card: ModelCard | None = None,
                           reasoning_mode: str | None = None) -> dict[str, Any]:
    """Prove a declared boolean switch actually changes the rendered prompt.

    Renders the same messages with the switch as declared and with it negated.
    If the two strings are identical the kwarg is inert — the template has no
    such variable, or it was renamed upstream — and the run would silently
    execute the wrong reasoning condition. That is refused here.

    Empty kwargs are checked, not skipped. This function used to be called under
    `if requests and template_kwargs:`, so the one case it most needed to catch —
    a card that supplies no kwargs at all — was the one case that disabled it.
    An empty mapping is legitimate ONLY when the card declares no reasoning
    argument for any mode, as for Kimi-VL and Qwen3-4B-Instruct-2507. A card that
    declares switches for other modes but not this one is an omission, and is
    refused: that shape is how a mode silently inherits the template default.
    """
    if not template_kwargs:
        declared = dict(getattr(card, "template_kwargs_by_mode", {}) or {})
        if declared:
            raise TemplateSwitchError(
                f"no chat-template kwargs are declared for reasoning mode "
                f"{reasoning_mode!r} on "
                f"{getattr(card, 'model_id', 'this checkpoint')!r}, but the "
                f"card declares them for {sorted(declared)}. The mode would "
                f"render at the template's own default, which is a different "
                f"experimental condition from the one being recorded. Declare "
                f"the kwargs for this mode, or remove it from supported_modes.")
        return {"checked": [], "kwargs": {}, "no_reasoning_argument": True,
                "reasoning_mode": reasoning_mode}

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
    # `template_kwargs` is deliberately absent from this condition: an empty
    # mapping is the case the check exists for.
    if requests and verify_switch:
        # Against the engine's OWN tokenizer, before a token is generated.
        switch_evidence = verify_template_switch(
            tokenizer, requests[0], template_kwargs, card,
            run_plan.reasoning_mode)
        # And the whole card, not only the mode being run: a registry entry
        # that misdescribes any of its modes is wrong now, not once some later
        # run happens to exercise the bad one.
        switch_evidence["card"] = validate_reasoning_control(
            card, tokenizer, requests[0])

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
