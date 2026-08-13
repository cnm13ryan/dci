"""Hugging Face Transformers backend: cells 132 + 192(torch branch), verbatim.

This is the baseline engine v15 froze (`CFG.engine == "hf_transformers"`), on
CUDA and on ROCm alike: PyTorch's ROCm builds expose the HIP device through the
`torch.cuda` API, so `cuda:N` here addresses an AMD GPU on the workstation and
an NVIDIA GPU on Lambda. Which one actually ran is pinned by the hardware
execution class, not by this module.

Every scientific behavior of the notebook path is preserved: gating on Gate 0
and Gate M before any weight loads, immutable-revision loading, tokenizer and
chat-template fingerprinting with FrozenPlanMismatch on drift, left padding,
single-device placement asserts, warmup, per-batch seeding, decoding
parameters from CFG, EOS/pad accounting and per-row termination records.
torch and transformers are imported through the compat shim so this module
IMPORTS everywhere but only RUNS with a real GPU stack.
"""
from __future__ import annotations

import gc
import json
import time
from typing import Any, Optional

from dci.compat import (AutoModelForCausalLM, AutoTokenizer, require_torch,
                        torch)
from dci.exceptions import FrozenPlanMismatch
from dci.pipeline import state as S
from dci.provenance.hashes import sha, sha_text


def get_hf_token() -> Optional[str]:
    # --- moved verbatim from cells/132.py (Colab userdata branch retained as
    # an optional source; it simply fails closed off-Colab)
    import os
    token = os.environ.get("HF_TOKEN")
    if token:
        return token
    try:
        from google.colab import userdata  # type: ignore

        return userdata.get("HF_TOKEN")
    except Exception:
        return None


def fingerprint_tokenizer(tok) -> dict[str, str]:
    """Stable identity of the tokenizer and of the chat template it applies."""
    # --- moved verbatim from cells/132.py
    try:
        vocab = tok.get_vocab()
        vocab_sha = sha_text("\n".join(f"{k}\t{v}" for k, v in sorted(vocab.items())))
    except Exception:
        vocab_sha = "unavailable"
    special = getattr(tok, "special_tokens_map", {}) or {}
    tokenizer_sha = sha({"class": type(tok).__name__, "vocab": vocab_sha,
                         "special": special,
                         "model_max_length": getattr(tok, "model_max_length", None)})
    template = getattr(tok, "chat_template", None) or ""
    return {"tokenizer_sha256": tokenizer_sha,
            "chat_template_sha256": sha_text(template)}


class HFTransformersBackend:
    name = "hf_transformers"

    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None

    @property
    def tokenizer(self):
        return self._tokenizer

    def load_model(self):
        """Loaded lazily and only after Gate 0 and Gate M have passed."""
        # --- moved verbatim from cells/132.py load_model(); `global tokenizer,
        # model` became backend attributes mirrored into shared state so every
        # notebook-era reader (S.tokenizer / S.model) still sees them.
        CFG = S.CFG
        if CFG.dry_run:
            return None, None
        if self._model is not None:
            return self._tokenizer, self._model
        require_torch("model loading")
        S.require_gate("0_implementation", "M_measurement")

        dtype = getattr(torch, S.RESOLVED_DTYPE)
        token = get_hf_token()

        with S.phase("tokenizer_load"):
            self._tokenizer = AutoTokenizer.from_pretrained(
                CFG.model_id, revision=CFG.model_revision, token=token, use_fast=True)
        tokenizer = self._tokenizer
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"

        prints = fingerprint_tokenizer(tokenizer)
        for key, value in prints.items():
            existing = S.TOKENIZER_STATE.get(key)
            if existing not in (None, value):
                raise FrozenPlanMismatch(
                    f"{key} changed within this run: {existing[:12]} -> {value[:12]}. "
                    "Every batch already committed was generated under the previous "
                    "value. Start a new run directory rather than mixing them.")
            S.TOKENIZER_STATE[key] = value
        (S.CONFIG_DIR / "tokenizer_fingerprint.json").write_text(
            json.dumps({**prints, "model_id": CFG.model_id,
                        "model_revision": CFG.model_revision}, indent=2),
            encoding="utf-8")

        with S.phase("model_load"):
            self._model = AutoModelForCausalLM.from_pretrained(
                CFG.model_id, revision=CFG.model_revision, token=token, dtype=dtype,
                attn_implementation=CFG.attn_implementation,
                device_map={"": CFG.single_gpu_index}, low_cpu_mem_usage=True)
        model = self._model
        model.eval()

        placements = set(getattr(model, "hf_device_map", {}).values())
        if placements and placements != {CFG.single_gpu_index}:
            raise RuntimeError(
                f"model modules were placed on {sorted(placements)}. Automatic "
                "offload is not the intended single-GPU inference condition.")

        with S.phase("warmup"):
            warm = tokenizer("warm up", return_tensors="pt").to(
                f"cuda:{CFG.single_gpu_index}")
            with torch.inference_mode():
                model.generate(**warm, max_new_tokens=8, do_sample=False,
                               temperature=None, top_p=None, top_k=None)
            torch.cuda.synchronize()
        print({"profile": CFG.model_profile, "model": CFG.model_id,
               "revision": CFG.model_revision, "dtype": str(dtype),
               "tokenizer_sha256": prints["tokenizer_sha256"][:12],
               "chat_template_sha256": prints["chat_template_sha256"][:12]})
        S.tokenizer, S.model = tokenizer, model
        return tokenizer, model

    def free_model(self) -> None:
        # --- moved verbatim from cells/132.py free_model()
        self._model, self._tokenizer = None, None
        S.model, S.tokenizer = None, None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("model released")

    def generate(self, batch_rows: list[dict[str, Any]],
                 batch_seed: int) -> tuple[list[str], dict[str, Any]]:
        # --- moved verbatim from cells/192.py generate_batch (torch branch)
        CFG = S.CFG
        profile: dict[str, Any] = {}
        require_torch("scientific generation")
        self.load_model()
        S.set_all_seeds(batch_seed)
        tokenizer, model = self._tokenizer, self._model

        absent = [r["row_id"] for r in batch_rows if r["row_id"] not in S._PROMPT_IDS]
        if absent:
            raise RuntimeError(f"{len(absent)} rows were never pre-tokenised.")

        t0 = time.perf_counter()
        padded = tokenizer.pad({"input_ids": [S._PROMPT_IDS[r["row_id"]] for r in batch_rows]},
                               return_tensors="pt")
        profile["tokenize_seconds"] = time.perf_counter() - t0
        profile["input_tokens"] = int(padded["attention_mask"].sum())

        t0 = time.perf_counter()
        device = next(model.parameters()).device
        padded = {k: v.to(device) for k, v in padded.items()}
        torch.cuda.synchronize()
        profile["h2d_seconds"] = time.perf_counter() - t0

        width = padded["input_ids"].shape[1]
        torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()
        with torch.inference_mode():
            out = model.generate(
                **padded, max_new_tokens=CFG.max_new_tokens, do_sample=CFG.do_sample,
                # top_k is passed EXPLICITLY since v15.1. Omitting it left the
                # effective value to the library default (50) or the model's own
                # generation_config.json (Qwen2.5 ships 20), so the decoding
                # policy was model-dependent and absent from the fingerprint.
                temperature=CFG.temperature, top_p=CFG.top_p, top_k=CFG.top_k,
                pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id,
                use_cache=True)
        torch.cuda.synchronize()
        profile["generate_seconds"] = time.perf_counter() - t0

        generated = out[:, width:]
        # The pad token IS the EOS token here, so counting non-pad positions would
        # drop the terminal EOS and undercount every completed sequence by one.
        eos = tokenizer.eos_token_id
        lengths, terminations = [], []
        for r, row in zip(batch_rows, generated.tolist()):
            stop = next((i for i, t in enumerate(row) if t == eos), None)
            length = len(row) if stop is None else stop + 1
            lengths.append(length)
            # Per-row termination diagnostics. These are POST-TREATMENT: they are
            # reported by arm and never conditioned on.
            terminations.append({
                "row_id": r["row_id"],
                "generated_token_count": int(length),
                "ended_with_eos": bool(stop is not None),
                "hit_max_new_tokens": bool(length >= CFG.max_new_tokens),
                "output_truncated": bool(stop is None and length >= CFG.max_new_tokens),
                "stop_reason": ("eos" if stop is not None else
                                "max_new_tokens" if length >= CFG.max_new_tokens
                                else "unknown")})
        S.TERMINATION_RECORDS.extend(terminations)
        profile["output_tokens"] = int(sum(lengths))
        profile["n_hit_max_new_tokens"] = int(sum(t["hit_max_new_tokens"] for t in terminations))
        profile["peak_allocated_bytes"] = int(torch.cuda.max_memory_allocated())
        profile["peak_reserved_bytes"] = int(torch.cuda.max_memory_reserved())

        t0 = time.perf_counter()
        texts = tokenizer.batch_decode(generated, skip_special_tokens=True)
        profile["decode_seconds"] = time.perf_counter() - t0
        return texts, profile
