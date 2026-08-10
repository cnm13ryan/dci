tokenizer = None
model = None


def get_hf_token() -> Optional[str]:
    token = os.environ.get("HF_TOKEN")
    if token:
        return token
    try:
        from google.colab import userdata

        return userdata.get("HF_TOKEN")
    except Exception:
        return None


def fingerprint_tokenizer(tok) -> dict[str, str]:
    """Stable identity of the tokenizer and of the chat template it applies."""
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


def load_model():
    """Loaded lazily and only after Gate 0 and Gate M have passed."""
    global tokenizer, model
    if CFG.dry_run:
        return None, None
    if model is not None:
        return tokenizer, model
    require_gate("0_implementation", "M_measurement")

    dtype = getattr(torch, RESOLVED_DTYPE)
    token = get_hf_token()

    with phase("tokenizer_load"):
        tokenizer = AutoTokenizer.from_pretrained(
            CFG.model_id, revision=CFG.model_revision, token=token, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    prints = fingerprint_tokenizer(tokenizer)
    for key, value in prints.items():
        existing = TOKENIZER_STATE.get(key)
        if existing not in (None, value):
            raise FrozenPlanMismatch(
                f"{key} changed within this run: {existing[:12]} -> {value[:12]}. "
                "Every batch already committed was generated under the previous "
                "value. Start a new run directory rather than mixing them.")
        TOKENIZER_STATE[key] = value
    (CONFIG_DIR / "tokenizer_fingerprint.json").write_text(
        json.dumps({**prints, "model_id": CFG.model_id,
                    "model_revision": CFG.model_revision}, indent=2),
        encoding="utf-8")

    with phase("model_load"):
        model = AutoModelForCausalLM.from_pretrained(
            CFG.model_id, revision=CFG.model_revision, token=token, dtype=dtype,
            attn_implementation=CFG.attn_implementation,
            device_map={"": CFG.single_gpu_index}, low_cpu_mem_usage=True)
    model.eval()

    placements = set(getattr(model, "hf_device_map", {}).values())
    if placements and placements != {CFG.single_gpu_index}:
        raise RuntimeError(
            f"model modules were placed on {sorted(placements)}. Automatic "
            "offload is not the intended single-GPU inference condition.")

    with phase("warmup"):
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
    return tokenizer, model


def free_model() -> None:
    global tokenizer, model
    model, tokenizer = None, None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("model released")


print(f"Model loading is deferred and gated on Gate 0 and Gate M. Profile "
      f"{CFG.model_profile} pins {CFG.model_id} at {CFG.model_revision[:12]}.")
