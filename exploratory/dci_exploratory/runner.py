"""Generate and score the matched design on a local ROCm GPU.

Deliberately a small, direct HF Transformers loop rather than the confirmatory
`dci.inference.hf_transformers` backend: that backend refuses to load weights
until Gate 0 and Gate M have passed, which is exactly right for evidence and
exactly wrong for an exploratory probe that must not be able to satisfy those
gates. The scientific behaviours that matter are kept identical to it — left
padding, explicit `top_k`, EOS-inclusive length accounting, per-row termination
records, single-device placement.

The rule this module exists to enforce: **a technical failure is never a
behavioural failure.** If a row does not produce text, its `a_failure` is null
and it is counted in `technical_failures`, never as non-compliance with A.
"""
from __future__ import annotations

import json
import platform
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from dci_exploratory import harvest
from dci_exploratory.design import Row, Selection

EXPLORATORY_STAMP = "EXPLORATORY_NO_EVIDENCE"

# System-message variants. "" is the protocol's own message, unchanged.
#
# The anti-collapse scaffold lives HERE, not in the numbered constraint list, so
# that the list stays byte-identical and the instruction count stays at k=5 in
# both conditions. Adding it as a sixth numbered constraint would have changed
# the load and confounded the comparison the intervention exists to make.
#
# Round 4 adds the rest of the ladder. `one_sentence_per_line` keeps its name and
# its exact bytes so the D2 run stays comparable; the two new members are a
# WEAKER reminder and a SHAM.
#
# The sham is matched to `one_sentence_per_line` on form and length — the same
# three opening words, the same imperative, 37 characters against 36 — and is
# about style
# rather than about sentence boundaries. Without it, "adding any extra clause to
# the system message reduces failure" is not excluded, and the D2 recovery could
# be a demand-characteristic of a longer system message rather than of its
# content.
#
# The ladder ORDERING (none < weak < strong) is an assumption about instruction
# strength, not a measurement. It is stated here so that a result which violates
# it is visible as a violation rather than absorbed.
SCAFFOLDS: dict[str, str] = {
    "": "",
    "weak_reminder": " Remember that each sentence ends with a full stop.",
    "one_sentence_per_line": " Write each sentence on its own line.",
    "sham_plain_style": " Write each sentence in a plain style.",
}

# What it would MEAN to obey each scaffold literally, where that is mechanically
# checkable. `""` has nothing to obey; the sham deliberately asks for something
# no rule can score, which is what makes it a sham and is recorded as such rather
# than quietly scored against an invented proxy.
SCAFFOLD_COMPLIANCE: dict[str, str] = {
    "": "not applicable",
    "weak_reminder": "every sentence ends in a terminal mark",
    "one_sentence_per_line": "line count is at least the sentence count",
    "sham_plain_style": "not mechanically checkable (deliberate)",
}


def system_message_for(scaffold: str) -> str:
    """The protocol's system message, plus the named scaffold clause."""
    from dci_exploratory import harvest
    if scaffold not in SCAFFOLDS:
        raise KeyError(f"unknown scaffold {scaffold!r}; known: {sorted(SCAFFOLDS)}")
    return harvest.load().SYSTEM_MESSAGE + SCAFFOLDS[scaffold]


@dataclass(frozen=True)
class ModelConfig:
    """Everything about the model and decoding that the run record must pin."""
    model_id: str = "Qwen/Qwen3-4B-Instruct-2507"
    # Immutable commit, resolved against the Hub. "main" is mutable, so two runs
    # under it would not be the same experiment.
    revision: str = "cdbee75f17c01a7cc42f958dc650907174af0554"
    dtype: str = "bfloat16"
    device_index: int = 0
    attn_implementation: str = "sdpa"
    # NOT the protocol's 180. `dci.analysis.output_budget` states the case
    # against it in the repository's own words: "The generation ceiling is 180
    # TOKENS, and it is a property of the apparatus, not of the science", and
    # truncation "can invent or reverse a result".
    #
    # Stage A measured exactly that failure. B — "each sentence strictly longer
    # than the last" — implies a geometrically growing answer, and its isolated
    # runs averaged 180.0 generated tokens, i.e. 8 of 8 hit the cap, against
    # 67-163 for every reference. A censored answer loses its final sentences, so
    # the sentence COUNT that A is scored on is decided by the ceiling rather
    # than by the model. At 180 this study would measure the cap.
    #
    # 512 clears the observed requirement with room to spare. Truncation is still
    # recorded per row and reported per arm; it is never conditioned on, because
    # it is post-treatment.
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 0
    do_sample: bool = True
    batch_size: int = 16
    base_seed: int = 20260810
    # Qwen3.5 is a REASONING model: its chat template opens a `<think>` block by
    # default, so the first 512 generated tokens are a reasoning trace and the
    # answer is never reached. A run under that default measures the trace, not
    # the response, and is not comparable with a non-reasoning instruct model.
    # `enable_thinking=False` is the model's OWN documented non-thinking mode and
    # is what makes the comparison like-for-like; it is recorded per run rather
    # than assumed.
    disable_thinking: bool = False


class Backend:
    """One model on one GPU, loaded once."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.device = f"cuda:{config.device_index}"
        self.load_seconds = 0.0
        self.prompt_convention = "unknown"

    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if self.model is not None:
            return
        if not torch.cuda.is_available():
            raise RuntimeError(
                "no GPU visible to torch. This study is GPU-only by design: a CPU "
                "fallback would silently change the execution condition.")
        cfg = self.config
        started = time.perf_counter()
        self.tokenizer = AutoTokenizer.from_pretrained(
            cfg.model_id, revision=cfg.revision, use_fast=True)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        # Left padding: with right padding a decoder-only model would continue
        # from pad tokens and the generations would not correspond to the prompts.
        self.tokenizer.padding_side = "left"

        self.model = AutoModelForCausalLM.from_pretrained(
            cfg.model_id, revision=cfg.revision, dtype=getattr(torch, cfg.dtype),
            attn_implementation=cfg.attn_implementation,
            device_map={"": cfg.device_index}, low_cpu_mem_usage=True)
        self.model.eval()

        placements = set(getattr(self.model, "hf_device_map", {}).values())
        if placements and placements != {cfg.device_index}:
            raise RuntimeError(
                f"model modules were placed on {sorted(placements)}; automatic "
                "offload is not the intended single-GPU condition")
        self.load_seconds = time.perf_counter() - started

    def fingerprint(self) -> dict[str, Any]:
        from dci.provenance.hashes import sha, sha_text
        tok = self.tokenizer
        try:
            vocab = tok.get_vocab()
            vocab_sha = sha_text("\n".join(f"{k}\t{v}" for k, v in sorted(vocab.items())))
        except Exception:
            vocab_sha = "unavailable"
        template = getattr(tok, "chat_template", None) or ""
        return {
            "tokenizer_class": type(tok).__name__,
            "tokenizer_sha256": sha({"class": type(tok).__name__, "vocab": vocab_sha,
                                     "special": getattr(tok, "special_tokens_map", {}) or {}}),
            "chat_template_sha256": sha_text(template),
            "chat_template_present": bool(template),
            "model_class": type(self.model).__name__,
            "n_parameters": int(sum(p.numel() for p in self.model.parameters())),
            "model_dtype": str(next(self.model.parameters()).dtype),
            "eos_token_id": tok.eos_token_id,
            "pad_token_id": tok.pad_token_id,
        }

    def render(self, system_message: str, user_prompt: str) -> str:
        """The exact string handed to the model, chat template applied.

        Some instruction-tuned families — Gemma 2 among them — publish a chat
        template with no `system` role. Dropping the system message there would
        silently run a different experiment, and hand-writing a template would
        run a different one again. The fallback prepends the system message to
        the user turn, which is what those model cards themselves prescribe, and
        the substitution is recorded on the backend so the run summary can say
        which convention produced the prompts.
        """
        messages = [{"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}]
        extra = {"enable_thinking": False} if self.config.disable_thinking else {}
        try:
            rendered = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, **extra)
            self.prompt_convention = ("system+user, thinking disabled" if extra
                                      else "system+user")
            return rendered
        except Exception:                              # noqa: BLE001 - see below
            merged = (f"{system_message}\n\n{user_prompt}" if system_message
                      else user_prompt)
            rendered = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": merged}],
                tokenize=False, add_generation_prompt=True, **extra)
            self.prompt_convention = ("system merged into first user turn"
                                      + (", thinking disabled" if extra else ""))
            return rendered

    def generate(self, prompts: list[str], batch_seed: int
                 ) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
        import torch
        from transformers import set_seed

        cfg = self.config
        set_seed(batch_seed)
        tok, model = self.tokenizer, self.model

        encoded = tok(prompts, return_tensors="pt", padding=True,
                      add_special_tokens=False).to(self.device)
        width = encoded["input_ids"].shape[1]

        torch.cuda.reset_peak_memory_stats(self.device)
        started = time.perf_counter()
        with torch.inference_mode():
            sampling = (dict(temperature=cfg.temperature, top_p=cfg.top_p,
                             top_k=cfg.top_k) if cfg.do_sample else {})
            out = model.generate(
                **encoded, max_new_tokens=cfg.max_new_tokens,
                do_sample=cfg.do_sample, **sampling,
                pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id,
                use_cache=True)
        torch.cuda.synchronize(self.device)
        elapsed = time.perf_counter() - started

        generated = out[:, width:]
        # The pad token IS the EOS token here, so counting non-pad positions
        # would drop the terminal EOS and undercount every finished sequence.
        eos_ids = tok.eos_token_id
        eos_ids = {eos_ids} if isinstance(eos_ids, int) else set(eos_ids or ())
        terminations = []
        for sequence in generated.tolist():
            stop = next((i for i, t in enumerate(sequence) if t in eos_ids), None)
            length = len(sequence) if stop is None else stop + 1
            terminations.append({
                "generated_token_count": int(length),
                "ended_with_eos": bool(stop is not None),
                "hit_max_new_tokens": bool(length >= cfg.max_new_tokens),
                "output_truncated": bool(stop is None and length >= cfg.max_new_tokens),
                "stop_reason": ("eos" if stop is not None else
                                "max_new_tokens" if length >= cfg.max_new_tokens
                                else "unknown"),
            })
        texts = tok.batch_decode(generated, skip_special_tokens=True)
        profile = {
            "batch_seed": batch_seed,
            "batch_rows": len(prompts),
            "prompt_width_tokens": int(width),
            "input_tokens": int(encoded["attention_mask"].sum()),
            "output_tokens": int(sum(t["generated_token_count"] for t in terminations)),
            "generate_seconds": elapsed,
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(self.device)),
            "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(self.device)),
        }
        return texts, terminations, profile


# ----------------------------------------------------------------- execution
def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), capture_output=True, text=True,
                              cwd=Path(__file__).resolve().parent).stdout.strip()
    except Exception:
        return ""


def run(rows: list[Row], selection: Selection, config: ModelConfig,
        out_dir: Path, stage: str) -> dict[str, Any]:
    """Generate, score, and write every artifact. Returns the run summary."""
    S = harvest.load()
    out_dir.mkdir(parents=True, exist_ok=True)

    backend = Backend(config)
    backend.load()

    # Deterministic batching: rows are ordered by row_id so the same design
    # produces the same batches, and therefore the same seeds, on every run.
    ordered = sorted(rows, key=lambda r: r.row_id)
    records: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    technical_failures: list[dict[str, Any]] = []
    started = time.perf_counter()

    for batch_index in range(0, len(ordered), config.batch_size):
        batch = ordered[batch_index:batch_index + config.batch_size]
        batch_seed = (config.base_seed + batch_index) % (2**31 - 1)
        rendered = [backend.render(system_message_for(getattr(r, "scaffold", "")),
                                   r.user_prompt) for r in batch]
        try:
            texts, terminations, profile = backend.generate(rendered, batch_seed)
        except Exception as exc:                      # noqa: BLE001 - recorded, not raised
            # A whole batch failing is a TECHNICAL failure. Every row in it gets a
            # null outcome; none of them becomes an A-failure.
            for row, prompt in zip(batch, rendered):
                technical_failures.append({"row_id": row.row_id,
                                           "kind": type(exc).__name__, "error": str(exc)[:500]})
                records.append(_record(row, prompt, None, None, None, selection,
                                       batch_seed, batch_index // config.batch_size,
                                       error=f"{type(exc).__name__}: {exc}"[:500]))
            continue

        profile["batch_index"] = batch_index // config.batch_size
        profiles.append(profile)
        for row, prompt, text, termination in zip(batch, rendered, texts, terminations):
            verification = None
            arm_verification = None
            error = None
            if not text.strip():
                # An empty generation cannot be scored for compliance. Calling it
                # a violation would manufacture failures out of a decoding fault.
                error = "empty generation"
                technical_failures.append({"row_id": row.row_id, "kind": "empty_generation",
                                           "error": error})
            else:
                try:
                    verification = S.verify(text, row.measured)
                except Exception as exc:              # noqa: BLE001
                    error = f"verifier raised {type(exc).__name__}: {exc}"[:500]
                    technical_failures.append({"row_id": row.row_id,
                                               "kind": "verifier_error", "error": error})
                # The arm's OWN constraint, scored on the same text. Without it
                # "the model traded A away to satisfy the added instruction" and
                # "the model failed both" are indistinguishable, and the first is
                # the claim the substitution account actually makes.
                if row.arm != row.measured:
                    try:
                        arm_verification = S.verify(text, row.arm)
                    except Exception:                 # noqa: BLE001 - diagnostic only
                        arm_verification = None
            records.append(_record(row, prompt, text, verification, termination,
                                   selection, batch_seed,
                                   batch_index // config.batch_size, error=error,
                                   arm_verification=arm_verification))

    wall_seconds = time.perf_counter() - started

    # ------------------------------------------------------------- artifacts
    (out_dir / "generations.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8")
    (out_dir / "technical_failures.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in technical_failures),
        encoding="utf-8")
    (out_dir / "batch_profiles.json").write_text(
        json.dumps(profiles, indent=2), encoding="utf-8")

    summary = {
        "stamp": EXPLORATORY_STAMP,
        "stage": stage,
        "n_rows": len(records),
        "n_technical_failures": len(technical_failures),
        "wall_seconds": wall_seconds,
        "model_load_seconds": backend.load_seconds,
        "total_output_tokens": sum(p["output_tokens"] for p in profiles),
        "tokens_per_second": (sum(p["output_tokens"] for p in profiles)
                              / max(sum(p["generate_seconds"] for p in profiles), 1e-9)),
        "peak_allocated_bytes": max((p["peak_allocated_bytes"] for p in profiles),
                                    default=0),
        "peak_reserved_bytes": max((p["peak_reserved_bytes"] for p in profiles), default=0),
        "model": asdict(config),
        "model_fingerprint": backend.fingerprint(),
        "prompt_convention": backend.prompt_convention,
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2),
                                              encoding="utf-8")
    return summary


def _record(row: Row, rendered_prompt: str, text: Optional[str], verification,
            termination: Optional[dict[str, Any]], selection: Selection,
            batch_seed: int, batch_index: int, error: Optional[str] = None,
            arm_verification=None) -> dict[str, Any]:
    """One scored row. `a_failure` is null whenever the row was not scorable."""
    S = harvest.load()

    status = getattr(verification, "status", None)
    binary_pass = getattr(verification, "binary_pass", None)
    # `unscorable` means the verifier could not form a verdict (e.g. no
    # sentences at all). That is a MEASUREMENT outcome, not compliance, and is
    # kept out of the failure numerator rather than counted as a violation.
    scorable = verification is not None and status != "unscorable"
    a_failure = (1 - int(binary_pass)) if scorable else None

    record = {
        **row.as_dict(),
        "stamp": EXPLORATORY_STAMP,
        "batch_seed": batch_seed,
        "batch_index": batch_index,
        "instructions": [S.INSTRUCTIONS[c][row.paraphrase_id] for c in row.ordered_ids],
        "system_message": system_message_for(getattr(row, "scaffold", "")),
        "rendered_prompt": rendered_prompt,
        "response": text,
        "verifier_status": status,
        "verifier_binary_pass": None if binary_pass is None else int(binary_pass),
        "verifier_continuous_score": (None if verification is None
                                      else float(verification.continuous_score)),
        "verifier_detail": None if verification is None else _jsonable(verification.detail),
        "scorable": bool(scorable),
        "a_failure": a_failure,
        "arm_status": getattr(arm_verification, "status", None),
        "arm_binary_pass": (None if arm_verification is None
                            or arm_verification.binary_pass is None
                            else int(arm_verification.binary_pass)),
        "arm_scorable": bool(arm_verification is not None
                             and getattr(arm_verification, "status", None) != "unscorable"),
        "arm_detail": (None if arm_verification is None
                       else _jsonable(arm_verification.detail)),
        "technical_failure": error is not None,
        "error": error,
        "response_chars": None if text is None else len(text),
        "response_words": None if text is None else len(text.split()),
        "focal_id": selection.focal,
        "target_id": selection.target,
        "background": list(selection.background),
    }
    record.update(termination or {"generated_token_count": None, "ended_with_eos": None,
                                  "hit_max_new_tokens": None, "output_truncated": None,
                                  "stop_reason": None})
    return record


def _jsonable(value: Any) -> Any:
    """numpy scalars and arrays leak out of the verifiers; JSON cannot take them."""
    import numpy as np
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    return value


def environment_record() -> dict[str, Any]:
    """Everything needed to say which machine and which code produced a run."""
    from dci_exploratory import rocm_doctor
    record = rocm_doctor.collect()
    record.update({
        "git_commit": _git("rev-parse", "HEAD"),
        "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "git_worktree": _git("rev-parse", "--show-toplevel"),
        "hostname": platform.node(),
    })
    return record
