"""Transformers execution of the two-phase splice, shared by every family.

Why Transformers and not vLLM, which produced the canonical Qwen3-4B result:
vLLM is not installed on this machine and no ROCm build of it is present (see
`CROSS_MODEL_EXECUTION_MATRIX.md`). Transformers is the one backend that loads
all the tested architectures on gfx1100, so running every checkpoint through it
keeps the five-way comparison internally consistent. The cost is that
comparisons against the historical vLLM result are backend-confounded, which is
recorded rather than glossed.

Two execution details here are family-specific and both would silently corrupt
the science if handled generically:

**Decoding must not skip special tokens.** Qwen3.5 writes `<think>`/`</think>`
as ordinary vocabulary items that survive `skip_special_tokens=True`. Gemma 4
writes its reasoning channel as `<|channel>thought ... <channel|>`, and those ARE
special tokens: decoded the Qwen way they vanish, the boundary disappears, and
the scratchpad merges into the answer — precisely the failure the validity gate
exists to prevent. So every family decodes with `skip_special_tokens=False` and
then removes its OWN control tokens, keeping the reasoning delimiters.

**Stopping happens on token ids, not on strings.** Where a family's think-close
marker is a single vocabulary item, it is added to `eos_token_id` for the
reasoning phase. That is exact and cheap, and closure becomes an unambiguous
property of the emitted ids rather than of a substring search over text that a
detokeniser may have reflowed.

Seeding under batching — stated plainly because it is the one place where an
execution detail touches a scientific requirement:

* Each row carries a `scientific_seed`, a pure function of its scientific
  identity (`crossmodel.seeds`). Nothing about position, order, device or shard
  enters it.
* Transformers seeds one global RNG per `generate()` call, not one per sequence.
  Running rows one at a time would honour the per-row seed exactly but costs
  roughly an order of magnitude in wall-clock across five checkpoints.
* So batches are formed by the CALLER from a row-identity ordering, and the
  generator is seeded per batch with a digest of that batch's own row seeds.
  The realised sample for a row is therefore still a deterministic function of
  scientific identity alone — re-shard, re-merge or re-run and a row lands in the
  same batch at the same offset with the same stream.

What that regime must deliver scientifically is that nominal replicates are
independent draws, and that is checked empirically on the output rather than
assumed: `seeds.replicate_duplication` counts identical replicate pairs and the
runner refuses a file above the repository's 25% alarm threshold. Set
`batch_size=1` for exact per-row seeding when validating.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any, Optional, Sequence

from crossmodel.adapters.base import (Generation, GenerationConfig,
                                      ModelAdapter)
from crossmodel.contract import ReasoningMode


def batch_seed_for(seeds: Sequence[int]) -> int:
    """A batch's generator seed, derived from its members' scientific seeds."""
    material = "|".join(str(s) for s in seeds)
    return int.from_bytes(
        hashlib.sha256(material.encode()).digest()[:4], "big")


def _find(haystack: Sequence[int], needle: Sequence[int], start: int = 0
          ) -> int:
    """Index of the first occurrence of `needle` in `haystack`, or -1."""
    if not needle:
        return -1
    limit = len(haystack) - len(needle)
    for index in range(max(start, 0), limit + 1):
        if list(haystack[index:index + len(needle)]) == list(needle):
            return index
    return -1


class TransformersAdapter(ModelAdapter):
    """Everything family-independent about running the splice on Transformers."""

    #: Class used for text-only loading, e.g. "Qwen3_5ForCausalLM". When a
    #: checkpoint is multimodal but the study is text-only, loading the causal-LM
    #: class avoids allocating a vision tower that no DCI prompt ever uses.
    TEXT_ONLY_CLASS: Optional[str] = None
    #: Fallback when the text-only class cannot consume the checkpoint.
    FULL_CLASS: Optional[str] = None
    #: Extra kwargs for `from_pretrained` (e.g. trust_remote_code).
    LOAD_KWARGS: dict[str, Any] = {}
    #: Extra control tokens stripped from decoded text, beyond the ones the
    #: tokenizer itself declares. The reasoning delimiters are never stripped.
    CONTROL_TOKENS: tuple[str, ...] = ()
    #: Tokens that must SURVIVE cleaning because they carry the reasoning
    #: boundary. Defaults to the family's delimiters; a family whose delimiter is
    #: a composite of a special token and a channel name overrides this with the
    #: special tokens themselves.
    PRESERVE_TOKENS: tuple[str, ...] = ()

    #: How reasoning and answer are separated for this family.
    #:
    #: ``"splice"`` — stop the generation at the think-close marker, then
    #: re-prompt past it for the answer. Correct only where the chat template
    #: PRE-OPENS the reasoning block, so the model is already inside the trace
    #: when generation starts and cannot emit answer text before it. Qwen3.5
    #: does exactly that; it is also the canonical run's mechanism, so Qwen keeps
    #: the study's existing semantics including the separate answer allowance.
    #:
    #: ``"single_phase"`` — one unbroken generation, split afterwards by the
    #: family's own documented parser. Correct where the template does NOT force
    #: the model into a reasoning block first. Gemma 4 was observed emitting the
    #: answer BEFORE its thought channel on easy prompts and after it on the DCI
    #: prompts; a splice would have captured that leading answer text as
    #: "reasoning" and then scored a second, regenerated answer. Splitting after
    #: the fact is agnostic to the order the model chose.
    GENERATION_STRATEGY: str = "splice"

    # ------------------------------------------------------------- identity
    def resolve_revision(self) -> str:
        """Pin the checkpoint to a commit sha before any scientific generation."""
        if self._revision and len(self._revision) == 40:
            return self._revision
        from huggingface_hub import HfApi

        try:
            info = HfApi().model_info(self.MODEL_ID, revision=self._revision)
        except Exception as error:                      # noqa: BLE001
            raise RuntimeError(
                f"{self.MODEL_ID}: could not resolve an exact revision "
                f"({type(error).__name__}: {error}). Proceeding on a mutable "
                "alias would leave the run unable to say what it executed."
            ) from error
        sha = getattr(info, "sha", None)
        if not sha or len(sha) != 40:
            raise RuntimeError(
                f"{self.MODEL_ID}: the hub returned no commit sha; refusing to "
                "run an unpinned checkpoint")
        self._revision = sha
        return sha

    # ------------------------------------------------------------ lifecycle
    def load(self) -> None:
        import torch
        import transformers

        revision = self.resolve_revision()
        dtype = getattr(torch, self._dtype)

        tokenizer = transformers.AutoTokenizer.from_pretrained(
            self.MODEL_ID, revision=revision, **self.LOAD_KWARGS)
        # Decoder-only batching requires left padding, or generation continues
        # from pad tokens and every short prompt is corrupted.
        tokenizer.padding_side = "left"
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        before = self._memory_snapshot()
        model, loaded_as, multimodal = self._load_weights(revision, dtype)
        model.eval()
        after = self._memory_snapshot()

        self._model = model
        self._tokenizer = tokenizer
        self._load_metadata.update({
            "loaded_class": loaded_as,
            "multimodal_weights_allocated": multimodal,
            "tokenizer_revision": revision,
            "gpu_memory_before_load_gib": before,
            "gpu_memory_after_load_gib": after,
            "chat_template_identifier": self._chat_template_identifier(tokenizer),
            "chat_template_sha256": self._chat_template_hash(tokenizer),
            "think_close_token_ids": self._close_token_ids(),
        })

    def _load_weights(self, revision: str, dtype) -> tuple[Any, str, bool]:
        """Prefer a text-only class; verify it actually received the weights.

        A text-only class whose parameter names do not match the checkpoint's
        layout does NOT raise. `from_pretrained` reports the unmatched
        parameters as "missing" and silently initialises them at random, and the
        result is a model that loads, generates, and emits multilingual noise.
        That happened here on the first Gemma 4 attempt: `Gemma4ForCausalLM`
        against a `Gemma4ForConditionalGeneration` checkpoint left every weight
        missing, and the smoke answers were gibberish that a verifier would have
        scored as an ordinary failure to write four sentences.

        So the missing-key report is inspected, not the exception alone. Any
        missing parameter disqualifies the text-only path and the full class is
        used instead — with the vision tower allocated, and that fact recorded.
        """
        import transformers

        kwargs = dict(revision=revision, dtype=dtype,
                      device_map=self._device_map, **self.LOAD_KWARGS)

        if self.TEXT_ONLY_CLASS:
            try:
                cls = getattr(transformers, self.TEXT_ONLY_CLASS)
                model, info = cls.from_pretrained(
                    self.MODEL_ID, output_loading_info=True, **kwargs)
                missing = list(info.get("missing_keys") or [])
                if missing:
                    self._load_metadata["text_only_load_rejected"] = (
                        f"{len(missing)} parameter(s) were not found in the "
                        f"checkpoint and would have been randomly initialised, "
                        f"e.g. {missing[:3]}")
                    del model
                    self._free()
                else:
                    self._load_metadata["text_only_unexpected_keys"] = len(
                        info.get("unexpected_keys") or [])
                    return model, self.TEXT_ONLY_CLASS, False
            except Exception as error:                  # noqa: BLE001
                self._load_metadata["text_only_load_error"] = (
                    f"{type(error).__name__}: {str(error)[:400]}")
                self._free()

        name = self.FULL_CLASS or "AutoModelForCausalLM"
        cls = getattr(transformers, name)
        model, info = cls.from_pretrained(
            self.MODEL_ID, output_loading_info=True, **kwargs)
        missing = list(info.get("missing_keys") or [])
        if missing:
            raise RuntimeError(
                f"{self.MODEL_ID}: loading {name} left {len(missing)} "
                f"parameter(s) randomly initialised (e.g. {missing[:3]}). "
                "Generating from partially initialised weights would produce "
                "noise indistinguishable from a behavioural failure.")
        self._load_metadata["full_class_unexpected_keys"] = len(
            info.get("unexpected_keys") or [])
        return model, name, True

    @staticmethod
    def _free() -> None:
        import gc

        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def _memory_snapshot() -> dict[str, float]:
        import torch

        if not torch.cuda.is_available():
            return {}
        return {f"cuda:{i}": round(torch.cuda.memory_allocated(i) / 2 ** 30, 3)
                for i in range(torch.cuda.device_count())}

    @staticmethod
    def _chat_template_identifier(tokenizer) -> str:
        template = getattr(tokenizer, "chat_template", None)
        return "tokenizer.chat_template" if template else "none"

    @staticmethod
    def _chat_template_hash(tokenizer) -> str:
        template = getattr(tokenizer, "chat_template", None)
        if not template:
            return ""
        return hashlib.sha256(str(template).encode()).hexdigest()[:16]

    # ------------------------------------------------------------ rendering
    def render_prompt(self, messages: Sequence[dict[str, str]],
                      reasoning_mode: str) -> str:
        self.require_mode(reasoning_mode)
        tokenizer = self._require_tokenizer()
        return tokenizer.apply_chat_template(
            list(messages), tokenize=False, add_generation_prompt=True,
            **self.template_kwargs(reasoning_mode))

    def template_kwargs(self, reasoning_mode: str) -> dict[str, Any]:
        """The checkpoint's OWN documented reasoning switch. Overridden per family."""
        return {}

    # ----------------------------------------------------------- generation
    def generate(self, prompts: Sequence[str],
                 seeds: Sequence[tuple[int, int]],
                 generation_config: GenerationConfig) -> list[Generation]:
        self.require_mode(generation_config.reasoning_mode)
        if len(prompts) != len(seeds):
            raise ValueError("prompts and seeds must be the same length")
        started = time.perf_counter()

        if generation_config.reasoning_mode == ReasoningMode.NO_THINKING:
            results = self._generate_no_thinking(prompts, seeds,
                                                 generation_config)
        elif self.GENERATION_STRATEGY == "single_phase":
            results = self._generate_single_phase(prompts, seeds,
                                                  generation_config)
        else:
            results = self._generate_spliced(prompts, seeds, generation_config)

        elapsed = time.perf_counter() - started
        for result in results:
            result.latency_seconds = elapsed / max(len(results), 1)
        return results

    def _generate_no_thinking(self, prompts, seeds, config) -> list[Generation]:
        """Native non-thinking: the template already disabled the reasoning channel.

        There is no reasoning phase to run. Anything the model emits is the
        answer, and if a checkpoint emits a reasoning trace anyway that is a
        finding about the checkpoint, surfaced by the parser rather than hidden.
        """
        texts, finished, counts = self._raw_generate(
            prompts, [s[1] for s in seeds], config.max_answer_tokens,
            config, stop_on_think_close=False)

        results = []
        for prompt, text, reason, count, (seed_r, seed_a) in zip(
                prompts, texts, finished, counts, seeds):
            reasoning, answer = self.parse_output(text, config.reasoning_mode)
            results.append(Generation(
                prompt=prompt, raw_generation=text, reasoning_text=reasoning,
                final_answer=answer,
                # No reasoning phase ran, so realised reasoning is zero by
                # construction. A trace the parser still recovered is leakage,
                # reported by the validity gate rather than counted as thinking.
                reasoning_tokens=0,
                final_answer_tokens=count,
                finish_reason=reason,
                reasoning_emitted=self.reasoning_opened(text),
                natural_reasoning_closed=False,
                reasoning_cap_hit=False,
                answer_truncated=reason == "length",
                seed_reasoning=seed_r, seed_answer=seed_a,
                batch_seed=batch_seed_for([s[1] for s in seeds])))
        return results

    def _generate_spliced(self, prompts, seeds, config) -> list[Generation]:
        """Phase 1 reasoning to the think-close marker; phase 2 the answer."""
        close = self.THINK_CLOSE

        reasoning_raw, _, reasoning_counts = self._raw_generate(
            prompts, [s[0] for s in seeds], config.max_reasoning_tokens,
            config, stop_on_think_close=True)

        continued, reasoning_texts, closed_flags = [], [], []
        for prompt, text in zip(prompts, reasoning_raw):
            closed = close in text
            trace = text.split(close)[0] if closed else text
            trace = self.normalise_reasoning(trace)
            reasoning_texts.append(trace)
            closed_flags.append(closed)
            # The splice: whatever the model produced, then an explicit close,
            # so phase 2 begins exactly where an unbroken generation would have.
            continued.append(self.splice(prompt, trace))

        answer_raw, answer_finish, answer_counts = self._raw_generate(
            continued, [s[1] for s in seeds], config.max_answer_tokens,
            config, stop_on_think_close=False)

        results = []
        for i, prompt in enumerate(prompts):
            answer = self.clean_answer(answer_raw[i])
            results.append(Generation(
                prompt=prompt,
                raw_generation=(f"{reasoning_texts[i]}{close}\n\n"
                                f"{answer_raw[i]}"),
                reasoning_text=reasoning_texts[i],
                final_answer=answer,
                reasoning_tokens=reasoning_counts[i],
                final_answer_tokens=answer_counts[i],
                finish_reason=answer_finish[i],
                # The template pre-opened the block, so a trace was always
                # opened; the only question is whether the model closed it.
                reasoning_emitted=True,
                natural_reasoning_closed=closed_flags[i],
                reasoning_cap_hit=not closed_flags[i],
                answer_truncated=answer_finish[i] == "length",
                seed_reasoning=seeds[i][0], seed_answer=seeds[i][1],
                batch_seed=batch_seed_for([s[0] for s in seeds])))
        return results

    def _generate_single_phase(self, prompts, seeds, config
                               ) -> list[Generation]:
        """One unbroken generation, split afterwards by the family's parser.

        The budget is the engineering ceiling PLUS the answer allowance, so the
        answer always has at least as much room as it gets under the splice. It
        is not a separately enforced 512-token allowance, and that difference is
        recorded per row rather than assumed away: under this strategy a
        runaway trace can crowd the answer, which is why truncation and empty
        answers are measured and gate admission.
        """
        budget = config.max_reasoning_tokens + config.max_answer_tokens
        texts, finish, counts = self._raw_generate(
            prompts, [s[0] for s in seeds], budget, config,
            stop_on_think_close=False, return_ids=True)
        raw_texts, raw_ids = texts

        results = []
        for i, prompt in enumerate(prompts):
            reasoning, answer = self.parse_output(
                raw_texts[i], config.reasoning_mode)
            emitted = self.reasoning_opened(raw_texts[i])
            closed = self.THINK_CLOSE in raw_texts[i]
            reasoning_tokens, answer_tokens = self._split_token_counts(
                raw_ids[i], counts[i], emitted, closed)
            results.append(Generation(
                prompt=prompt, raw_generation=raw_texts[i],
                reasoning_text=reasoning, final_answer=answer,
                reasoning_tokens=reasoning_tokens,
                final_answer_tokens=answer_tokens,
                finish_reason=finish[i],
                reasoning_emitted=emitted,
                natural_reasoning_closed=closed,
                # The ceiling binds only when a trace was opened, never closed,
                # and the whole budget was consumed. A model that simply chose
                # not to think has not hit a ceiling.
                reasoning_cap_hit=(emitted and not closed
                                   and finish[i] == "length"),
                answer_truncated=finish[i] == "length",
                seed_reasoning=seeds[i][0], seed_answer=seeds[i][1],
                batch_seed=batch_seed_for([s[0] for s in seeds])))
        return results

    def reasoning_opened(self, raw_output: str) -> bool:
        """Did the model open a reasoning block at all?"""
        return self.THINK_OPEN in raw_output or self.THINK_CLOSE in raw_output

    def _split_token_counts(self, ids: list[int], total: int, emitted: bool,
                            closed: bool) -> tuple[int, int]:
        """Reasoning and answer token counts, measured in token space.

        Counted from the emitted ids rather than by re-encoding the split
        strings: re-encoding is only approximately inverse, and the
        reasoning-length distribution is a reported quantity.
        """
        if not emitted:
            # No reasoning block was opened, so every token is answer. Charging
            # them to reasoning would invent a trace the model never wrote.
            return 0, total
        tokenizer = self._require_tokenizer()
        close_ids = tokenizer.encode(self.THINK_CLOSE,
                                     add_special_tokens=False)
        open_ids = tokenizer.encode(self.THINK_OPEN, add_special_tokens=False)
        start = _find(ids, open_ids)
        first = start + len(open_ids) if start >= 0 else 0
        if not closed:
            # An unclosed trace: everything after the opener is scratch and
            # there is no answer to attribute tokens to.
            return max(total - first, 0), 0
        end = _find(ids, close_ids, first)
        if end < 0:
            return max(total - first, 0), 0
        return max(end - first, 0), max(total - (end + len(close_ids)), 0)

    def splice(self, prompt: str, trace: str) -> str:
        """Rebuild the continuation prompt for the answer phase."""
        return f"{prompt}{trace}{self.THINK_CLOSE}\n\n"

    def _close_token_ids(self) -> list[int]:
        """The think-close marker's ids, when it is a single vocabulary item."""
        tokenizer = self._tokenizer
        if tokenizer is None:
            return []
        ids = tokenizer.encode(self.THINK_CLOSE, add_special_tokens=False)
        return ids if len(ids) == 1 else []

    def _raw_generate(self, prompts: Sequence[str], seeds: Sequence[int],
                      max_new_tokens: int, config: GenerationConfig,
                      stop_on_think_close: bool, return_ids: bool = False
                      ) -> tuple[Any, list[str], list[int]]:
        """Returns per-row `(text, finish_reason, generated_token_count)`.

        The token count comes from the ids the model actually emitted, not from
        re-encoding the decoded string: re-encoding is only approximately
        inverse, and the reasoning-length distribution is a reported quantity.
        """
        import torch

        tokenizer = self._require_tokenizer()
        model = self._require_model()

        encoded = tokenizer(list(prompts), return_tensors="pt", padding=True,
                            add_special_tokens=False)
        device = next(model.parameters()).device
        encoded = {k: v.to(device) for k, v in encoded.items()}

        kwargs: dict[str, Any] = dict(
            max_new_tokens=max_new_tokens, do_sample=True,
            temperature=config.temperature, top_p=config.top_p,
            pad_token_id=tokenizer.pad_token_id,
            # Transformers defaults top_k to 50; the canonical run left it
            # unset. Passing 0 disables it, matching the canonical support.
            top_k=config.top_k if config.top_k > 0 else 0)

        close_ids = self._close_token_ids()
        eos = tokenizer.eos_token_id
        base_eos = [eos] if isinstance(eos, int) else list(eos or [])
        if stop_on_think_close:
            if close_ids:
                kwargs["eos_token_id"] = base_eos + close_ids
            else:
                # No single-token marker: fall back to string stopping.
                kwargs["stop_strings"] = [self.THINK_CLOSE]
                kwargs["tokenizer"] = tokenizer

        torch.manual_seed(batch_seed_for(seeds))
        with torch.no_grad():
            output = model.generate(**encoded, **kwargs)

        prompt_length = encoded["input_ids"].shape[1]
        generated = output[:, prompt_length:]
        pad_id = tokenizer.pad_token_id

        texts, finish, counts, kept_ids = [], [], [], []
        for i in range(generated.shape[0]):
            ids = generated[i].tolist()
            # Rows that finished early are right-padded while the batch's
            # slowest row continues. Trim that padding before counting.
            end = len(ids)
            while end > 0 and ids[end - 1] == pad_id:
                end -= 1
            real = ids[:end]
            # skip_special_tokens=False: a family whose reasoning delimiters are
            # special tokens would otherwise lose them, and with them the
            # boundary between scratchpad and answer.
            text = self._clean_decoded(
                tokenizer.decode(real, skip_special_tokens=False))

            stopped = bool(set(real) & set(base_eos + (close_ids if
                                                       stop_on_think_close
                                                       else [])))
            hit_length = len(real) >= max_new_tokens and not stopped
            texts.append(text)
            counts.append(len(real))
            kept_ids.append(real)
            finish.append("length" if hit_length else "stop")
        if return_ids:
            return (texts, kept_ids), finish, counts
        return texts, finish, counts

    def _strip_tokens(self) -> list[str]:
        """Every special token except the ones carrying the reasoning boundary.

        Derived from the tokenizer rather than hand-listed per family. Hand
        lists rot: the first Qwen smoke run left `<|im_end|>` on the end of every
        answer, and that string would have gone to a sentence-count verifier as
        if it were prose. Asking the tokenizer which tokens are control tokens
        makes the omission impossible instead of merely unlikely.
        """
        cached = getattr(self, "_strip_cache", None)
        if cached is not None:
            return cached
        tokenizer = self._tokenizer
        declared: list[str] = []
        if tokenizer is not None:
            declared = [str(t) for t in
                        (getattr(tokenizer, "all_special_tokens", None) or [])]
            extra = getattr(tokenizer, "additional_special_tokens", None) or []
            declared += [str(t) for t in extra]
        preserve = set(self.PRESERVE_TOKENS or
                       (self.THINK_OPEN, self.THINK_CLOSE))
        tokens = {t for t in declared + list(self.CONTROL_TOKENS)
                  if t and t not in preserve}
        # Longest first, so a token that contains another is removed whole.
        self._strip_cache = sorted(tokens, key=len, reverse=True)
        return self._strip_cache

    def _clean_decoded(self, text: str) -> str:
        """Remove control tokens, keeping the reasoning delimiters."""
        for token in self._strip_tokens():
            if token in text:
                text = text.replace(token, "")
        return text

    # -------------------------------------------------------------- parsing
    def normalise_reasoning(self, trace: str) -> str:
        """Strip a leading open marker the template may or may not have emitted.

        Qwen3.5's template pre-opens `<think>\\n` in the generation prompt, so the
        completion does NOT repeat it; Qwen3's did not, so the completion did.
        Both normalise to a trace without its opening delimiter, and the
        delimiters themselves are recorded in `execution_metadata`.
        """
        text = trace
        if text.lstrip().startswith(self.THINK_OPEN):
            text = text.lstrip()[len(self.THINK_OPEN):]
        return text.strip("\n")

    def clean_answer(self, text: str) -> str:
        return text.strip()

    def parse_output(self, raw_output: str, reasoning_mode: str
                     ) -> tuple[str, str]:
        """Total split of a raw generation into reasoning and answer.

        Never returns the trace as the answer: a response that closed no
        reasoning block in a thinking mode yields an EMPTY answer, which the
        validity gate then counts as a failure to produce an answer rather than
        letting a scratchpad reach a verifier.
        """
        open_marker, close = self.THINK_OPEN, self.THINK_CLOSE

        if close in raw_output:
            head, _, tail = raw_output.partition(close)
            if open_marker in head:
                # Content can precede the reasoning block on families whose
                # template does not force the model into it. That leading text
                # is ANSWER, not reasoning, and joining it to the trailing text
                # is what keeps the split agnostic to the order the model chose.
                leading, _, reasoning = head.partition(open_marker)
            else:
                leading, reasoning = "", head
            answer = f"{leading.strip()}\n{tail.strip()}".strip()
            return reasoning.strip("\n"), self.clean_answer(answer)

        if reasoning_mode == ReasoningMode.NO_THINKING:
            # No reasoning block was expected and none was closed: the whole
            # completion is the answer. An unclosed OPEN marker is still a
            # finding, so it is surfaced as reasoning with no answer.
            if open_marker in raw_output:
                return raw_output.split(open_marker, 1)[1].strip("\n"), ""
            return "", self.clean_answer(raw_output)

        # A thinking mode that never closed its block: all scratch, no answer.
        reasoning = raw_output
        if open_marker in reasoning:
            reasoning = reasoning.split(open_marker, 1)[1]
        return reasoning.strip("\n"), ""
