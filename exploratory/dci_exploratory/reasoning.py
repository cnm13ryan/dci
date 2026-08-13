"""A hard reasoning-budget harness: two-phase generation with separate channels.

`max_new_tokens` is **not** a reasoning budget. Capping a single generate() call
truncates whatever the model happens to be emitting, so a small cap yields *no
final answer at all* rather than a short-reasoning answer, and the comparison
across caps confounds "less reasoning" with "no response". Round 7 recorded that
as the reason the reasoning stage had not been run.

What this module does instead, for a model whose chat template opens an explicit
reasoning block:

  **Phase 1 — reasoning, budget `b`.** The prompt already ends with `<think>\\n`.
  Generate at most `b` tokens with `</think>` as a stop token. A sequence that
  emits `</think>` has finished thinking naturally; one that does not has hit the
  cap.

  **Phase 2 — answer, budget FIXED.** The reasoning text is appended to the
  prompt, closed with `</think>` if the model did not close it itself, and a
  fresh generation produces the final answer under a budget that is the **same
  in every treatment**.

That gives the four properties Stage 0.3 demands: budgets genuinely change the
reasoning resource; an answer is always obtainable after exhaustion; the
answer budget is constant across treatments; and the verifier sees a comparable
final-answer surface in every cell.

The two channels are never mixed. `response` is phase 2 only; the reasoning text
is stored separately as `reasoning`. A verifier never sees the reasoning.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

THINK_OPEN = "<think>"
THINK_CLOSE = "</think>"


@dataclass(frozen=True)
class BudgetResult:
    """One row's two-phase generation, with both channels kept apart."""
    reasoning: str
    answer: str
    reasoning_tokens: int
    answer_tokens: int
    reasoning_cap_hit: bool
    closed_naturally: bool
    answer_ended_with_eos: bool
    answer_truncated: bool
    reasoning_seconds: float
    answer_seconds: float


class ReasoningBackend:
    """Wraps a loaded `runner.Backend` with two-phase budgeted generation."""

    def __init__(self, backend, answer_tokens: int = 320):
        self.backend = backend
        self.answer_tokens = answer_tokens
        self._close_id: Optional[int] = None

    # ------------------------------------------------------------- validation
    def supports_reasoning(self) -> tuple[bool, str]:
        """Can this checkpoint expose a reasoning channel we can budget?

        Returns (ok, reason). A model whose template does not open a reasoning
        block cannot be given a reasoning budget by this method, and that is
        reported as a blocker rather than approximated.
        """
        tok = self.backend.tokenizer
        template = getattr(tok, "chat_template", None) or ""
        if THINK_OPEN not in template:
            return False, (f"the chat template never emits {THINK_OPEN!r}, so "
                           "there is no reasoning phase to budget")
        ids = tok.encode(THINK_CLOSE, add_special_tokens=False)
        if len(ids) != 1:
            return False, (f"{THINK_CLOSE!r} is not a single token ({ids}); the "
                           "stop-token approach would be unreliable")
        self._close_id = ids[0]
        rendered = tok.apply_chat_template(
            [{"role": "user", "content": "x"}], tokenize=False,
            add_generation_prompt=True)
        if not rendered.rstrip().endswith(THINK_OPEN):
            return False, ("the generation prompt does not end inside an open "
                           f"reasoning block (tail {rendered[-30:]!r})")
        return True, "ok"

    # ------------------------------------------------------------- generation
    def generate(self, prompts: list[str], budget: int, batch_seed: int
                 ) -> tuple[list[BudgetResult], dict[str, Any]]:
        import torch
        from transformers import set_seed

        cfg = self.backend.config
        tok, model = self.backend.tokenizer, self.backend.model
        device = self.backend.device
        assert self._close_id is not None, "call supports_reasoning() first"

        def _sampling() -> dict[str, Any]:
            return (dict(temperature=cfg.temperature, top_p=cfg.top_p,
                         top_k=cfg.top_k) if cfg.do_sample else {})

        # ---- phase 1: reasoning, stop at </think>, hard cap at `budget` -----
        set_seed(batch_seed)
        started = time.perf_counter()
        reasoning_texts: list[str] = []
        r_tokens: list[int] = []
        closed: list[bool] = []
        if budget > 0:
            encoded = tok(prompts, return_tensors="pt", padding=True,
                          add_special_tokens=False).to(device)
            width = encoded["input_ids"].shape[1]
            with torch.inference_mode():
                out = model.generate(
                    **encoded, max_new_tokens=budget, do_sample=cfg.do_sample,
                    **_sampling(), pad_token_id=tok.pad_token_id,
                    eos_token_id=[self._close_id, tok.eos_token_id],
                    use_cache=True)
            torch.cuda.synchronize(device)
            for sequence in out[:, width:].tolist():
                stop = next((i for i, t in enumerate(sequence)
                             if t == self._close_id), None)
                body = sequence if stop is None else sequence[:stop]
                # drop trailing pad so the token count is the reasoning length
                pad = tok.pad_token_id
                while body and body[-1] == pad:
                    body.pop()
                reasoning_texts.append(tok.decode(body, skip_special_tokens=True))
                r_tokens.append(len(body))
                closed.append(stop is not None)
        else:
            reasoning_texts = [""] * len(prompts)
            r_tokens = [0] * len(prompts)
            closed = [True] * len(prompts)
        reasoning_seconds = time.perf_counter() - started

        # ---- phase 2: the answer, under a FIXED budget in every treatment ---
        # The reasoning block is closed explicitly when the model did not close
        # it, so every cell hands the answer phase the same shape of context.
        continued = [
            f"{p}{r}{'' if c else ''}{THINK_CLOSE}\n\n"
            for p, r, c in zip(prompts, reasoning_texts, closed)]
        set_seed(batch_seed + 1)
        started = time.perf_counter()
        encoded = tok(continued, return_tensors="pt", padding=True,
                      add_special_tokens=False).to(device)
        width = encoded["input_ids"].shape[1]
        torch.cuda.reset_peak_memory_stats(device)
        with torch.inference_mode():
            out = model.generate(
                **encoded, max_new_tokens=self.answer_tokens,
                do_sample=cfg.do_sample, **_sampling(),
                pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id,
                use_cache=True)
        torch.cuda.synchronize(device)
        answer_seconds = time.perf_counter() - started

        eos_ids = tok.eos_token_id
        eos_ids = {eos_ids} if isinstance(eos_ids, int) else set(eos_ids or ())
        results: list[BudgetResult] = []
        for i, sequence in enumerate(out[:, width:].tolist()):
            stop = next((j for j, t in enumerate(sequence) if t in eos_ids), None)
            length = len(sequence) if stop is None else stop + 1
            results.append(BudgetResult(
                reasoning=reasoning_texts[i], answer=tok.decode(
                    sequence[:length], skip_special_tokens=True).strip(),
                reasoning_tokens=r_tokens[i], answer_tokens=int(length),
                reasoning_cap_hit=(not closed[i]) and budget > 0,
                closed_naturally=closed[i],
                answer_ended_with_eos=stop is not None,
                answer_truncated=stop is None and length >= self.answer_tokens,
                reasoning_seconds=reasoning_seconds / len(prompts),
                answer_seconds=answer_seconds / len(prompts)))
        profile = {
            "batch_seed": batch_seed, "batch_rows": len(prompts),
            "reasoning_budget": budget,
            "answer_token_budget": self.answer_tokens,
            "reasoning_tokens": sum(r_tokens),
            "answer_tokens": sum(r.answer_tokens for r in results),
            "reasoning_seconds": reasoning_seconds,
            "answer_seconds": answer_seconds,
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
        }
        return results, profile


# --------------------------------------------------------------- run driver
def run(rows, selection, config, out_dir, stage: str, budgets: list[int],
        answer_tokens: int = 320) -> dict[str, Any]:
    """Generate every row at every reasoning budget. Scores the ANSWER only."""
    import json
    from dataclasses import asdict
    from pathlib import Path

    from dci_exploratory import harvest, runner

    S = harvest.load()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    backend = runner.Backend(config)
    backend.load()
    engine = ReasoningBackend(backend, answer_tokens=answer_tokens)
    ok, why = engine.supports_reasoning()
    if not ok:
        raise RuntimeError(
            f"{config.model_id} cannot be given a hard reasoning budget: {why}. "
            "Stage 0.3 forbids pretending max_new_tokens is a reasoning budget, "
            "so this is recorded as a blocker rather than approximated.")

    ordered = sorted(rows, key=lambda r: r.row_id)
    records, profiles, technical = [], [], []
    started = time.perf_counter()
    for budget in budgets:
        for index in range(0, len(ordered), config.batch_size):
            batch = ordered[index:index + config.batch_size]
            seed = (config.base_seed + index) % (2**31 - 1)
            rendered = [backend.render(runner.system_message_for(
                getattr(r, "scaffold", "")), r.user_prompt) for r in batch]
            try:
                results, profile = engine.generate(rendered, budget, seed)
            except Exception as exc:                       # noqa: BLE001
                # A failed batch must still leave a ROW behind, with a null
                # outcome. The first version only appended to `technical` and
                # continued, so an OOM produced a run directory with zero
                # generations — indistinguishable at a glance from a run that
                # simply had nothing to do. `runner.run` has always recorded
                # null rows here and this now matches it.
                for row, prompt in zip(batch, rendered):
                    technical.append({"row_id": row.row_id, "budget": budget,
                                      "kind": type(exc).__name__,
                                      "error": str(exc)[:400]})
                    base = runner._record(row, prompt, None, None, None, selection,
                                          seed, index // config.batch_size,
                                          error=f"{type(exc).__name__}: {exc}"[:400])
                    base.update({"reasoning_budget": budget, "reasoning": None,
                                 "reasoning_tokens": None,
                                 "reasoning_cap_hit": None,
                                 "reasoning_closed_naturally": None,
                                 "answer_tokens": None,
                                 "answer_token_budget": answer_tokens,
                                 "row_id": f"{row.row_id}b{budget}"})
                    records.append(base)
                continue
            profile["batch_index"] = index // config.batch_size
            profiles.append(profile)
            for row, prompt, res in zip(batch, rendered, results):
                verification = arm_v = None
                error = None
                if not res.answer.strip():
                    error = "empty final answer"
                    technical.append({"row_id": row.row_id, "budget": budget,
                                      "kind": "empty_answer", "error": error})
                else:
                    try:
                        verification = S.verify(res.answer, row.measured)
                    except Exception as exc:               # noqa: BLE001
                        error = f"verifier raised {type(exc).__name__}"
                        technical.append({"row_id": row.row_id, "budget": budget,
                                          "kind": "verifier_error", "error": error})
                    if row.arm != row.measured:
                        try:
                            arm_v = S.verify(res.answer, row.arm)
                        except Exception:                  # noqa: BLE001
                            arm_v = None
                    # the background-slot occupant is a TREATMENT here, so its
                    # own compliance is measured rather than assumed
                variant = getattr(row, "variant", "")
                var_v = None
                if variant and res.answer.strip():
                    try:
                        var_v = S.verify(res.answer, variant)
                    except Exception:                      # noqa: BLE001
                        var_v = None
                base = runner._record(row, prompt, res.answer, verification, None,
                                      selection, seed, index // config.batch_size,
                                      error=error, arm_verification=arm_v)
                base.update({
                    "reasoning_budget": budget,
                    "reasoning": res.reasoning,
                    "reasoning_tokens": res.reasoning_tokens,
                    "reasoning_cap_hit": res.reasoning_cap_hit,
                    "reasoning_closed_naturally": res.closed_naturally,
                    "answer_tokens": res.answer_tokens,
                    "answer_token_budget": answer_tokens,
                    "total_generated_tokens": res.reasoning_tokens + res.answer_tokens,
                    "reasoning_seconds": res.reasoning_seconds,
                    "answer_seconds": res.answer_seconds,
                    "total_seconds": res.reasoning_seconds + res.answer_seconds,
                    "ended_with_eos": res.answer_ended_with_eos,
                    "output_truncated": res.answer_truncated,
                    "generated_token_count": res.answer_tokens,
                    "variant_status": getattr(var_v, "status", None),
                    "variant_binary_pass": (None if var_v is None
                                            or var_v.binary_pass is None
                                            else int(var_v.binary_pass)),
                    "row_id": f"{row.row_id}b{budget}",
                })
                records.append(base)

    wall = time.perf_counter() - started
    (out_dir / "generations.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8")
    (out_dir / "technical_failures.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in technical),
        encoding="utf-8")
    (out_dir / "batch_profiles.json").write_text(json.dumps(profiles, indent=2),
                                                 encoding="utf-8")
    summary = {
        "stamp": runner.EXPLORATORY_STAMP, "stage": stage,
        "n_rows": len(records), "n_technical_failures": len(technical),
        "wall_seconds": wall, "model_load_seconds": backend.load_seconds,
        "reasoning_budgets": budgets, "answer_token_budget": answer_tokens,
        "total_output_tokens": sum(p["answer_tokens"] for p in profiles),
        "total_reasoning_tokens": sum(p["reasoning_tokens"] for p in profiles),
        "tokens_per_second": (sum(p["answer_tokens"] + p["reasoning_tokens"]
                                  for p in profiles)
                              / max(sum(p["reasoning_seconds"] + p["answer_seconds"]
                                        for p in profiles), 1e-9)),
        "peak_allocated_bytes": max((p["peak_allocated_bytes"] for p in profiles),
                                    default=0),
        "model": asdict(config), "model_fingerprint": backend.fingerprint(),
        "prompt_convention": backend.prompt_convention,
        "reasoning_harness": "two-phase: budgeted <think> then fixed-budget answer",
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2),
                                              encoding="utf-8")
    return summary
