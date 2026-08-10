def prompt_fingerprint(user_prompt: str) -> str:
    """Tokenizer-free identity of the text sent to the model."""
    return sha_text(SYSTEM_MESSAGE + "\x00" + user_prompt)


# ============================================== the synthetic dry-run oracle
# The oracle stands in for the model when DRY_RUN_MODE is on. Nothing it
# produces is evidence. Its one scientific duty is to exercise every branch of
# the pipeline, and that requires DYNAMIC RANGE: if the corpus cannot satisfy a
# constraint at all, that constraint's failure rate is pinned at 1.0 whatever
# the design does, every signature component is constant, and the gates fail for
# a reason that belongs to the fixture rather than to the machinery under test.
# So the corpus is composed feature by feature rather than written as prose, and
# Gate 0 asserts that every declared constraint is both satisfied and violated
# by it.
_SHORT = ("water gate flow bank level tide silt drift lock weir bed reach ford "
          "dune ridge marsh creek berm crest").split()
_LONG = ("pressure chamber gradient reservoir sediment boundary structure "
         "material capacity discharge turbulence conduit").split()
_VOWEL = "open edge inlet upper inner outer under above eddy apex oxbow".split()
_PWORD = "pipes packed porous ponds pools".split()
_LY = "slowly evenly aptly coyly".split()
_FORBIDDEN = list(CFG.u_forbidden_words)
_REQUIRED = list(CFG.u_required_words)
_LONG_LETTERS = CFG.long_word_letters

_INT_MODES: tuple[tuple[int, ...], ...] = (
    (), (7,), (12, 18), (10, 20, 30), (20, 30, 50), (2, 4, 6, 8),
    (5, 5, 5), (1, 2, 3, 4, 5), (25, 25, 50), (40, 60),
)


def _is_long(token: str) -> bool:
    return len(token) >= _LONG_LETTERS


def _is_vowel_initial(token: str) -> bool:
    return bool(token) and token[0].lower() in "aeiou"


def _compose_sentence(rng, n_words: int, *, first: Optional[str],
                      longs: int, vowels: int, p_words: int,
                      specials: list[str], ly: bool, caps: bool,
                      deck: Optional[list[str]]) -> list[str]:
    """A token list of exactly n_words honouring as many feature targets as fit.

    Priority order when the budget binds: the controlled first word, then the
    whole-text specials carried by this sentence, then the per-sentence feature
    counts, then filler. Truncation therefore removes filler first.
    """
    def draw(pool: list[str]) -> str:
        if deck is not None:
            for token in list(deck):
                if token in pool:
                    deck.remove(token)
                    return token
            return deck.pop() if deck else str(rng.choice(pool))
        return str(rng.choice(pool))

    tokens: list[str] = []
    if first is not None:
        tokens.append(first)
    tokens.extend(specials)
    if ly:
        tokens.append(draw(_LY))
    if caps:
        tokens.append(draw(_LONG).upper())
    while sum(_is_long(t) for t in tokens) < longs and len(tokens) < n_words:
        tokens.append(draw(_LONG))
    while sum(_is_vowel_initial(t) for t in tokens) < vowels and len(tokens) < n_words:
        tokens.append(draw(_VOWEL))
    while sum(t.lower().startswith("p") for t in tokens) < p_words and len(tokens) < n_words:
        tokens.append(draw(_PWORD))
    while len(tokens) < n_words:
        tokens.append(draw(_SHORT))
    return tokens[:max(1, n_words)]


def _render_sentence(tokens: list[str], *, commas: int, semicolons: int,
                     colons: int, parens: int, quotes: int,
                     question: bool, end_long: bool, rng) -> str:
    tokens = list(tokens)
    if end_long and len(tokens) > 1 and not _is_long(tokens[-1]):
        tokens[-1] = str(rng.choice(_LONG))
    if parens and len(tokens) >= 3:
        i = min(len(tokens) - 2, 1)
        tokens[i] = "(" + tokens[i]
        tokens[i + 1] = tokens[i + 1] + ")"
    if quotes and len(tokens) >= 3:
        i = min(len(tokens) - 2, len(tokens) // 2)
        tokens[i] = '"' + tokens[i]
        tokens[i + 1] = tokens[i + 1] + '"'
    # Punctuation is attached to existing tokens so the word count is exactly
    # the number of tokens: every length constraint reads what was designed.
    slots = [i for i in range(len(tokens) - 1)]
    rng.shuffle(slots)
    for mark, count in ((",", commas), (";", semicolons), (":", colons)):
        for _ in range(count):
            if not slots:
                break
            tokens[slots.pop()] += mark
    text = " ".join(tokens)
    text = text[0].upper() + text[1:] if text else text
    return text + ("?" if question else ".")


def _synthetic_variant(i: int) -> str:
    """One corpus item, composed so that every verifier's feature varies."""
    rng = np.random.default_rng(stable_int(f"corpus-v14b|{i}"))
    n_sent = int(rng.integers(2, 7))
    rising = bool(rng.random() < 0.45)
    base = int(rng.choice([4, 6, 8, 11, 14, 17, 21, 26, 31]))
    step = int(rng.choice([1, 2, 3, 5])) if rising else 0
    lengths = [max(3, base + step * s + (0 if rising else int(rng.integers(-2, 3))))
               for s in range(n_sent)]

    commas = int(rng.choice([0, 0, 1, 2]))
    semi_each = bool(rng.random() < 0.30)
    semi_total = 0 if semi_each else int(rng.choice([0, 0, 1, 2, 3]))
    colons_total = int(rng.choice([0, 0, 1, 2]))
    parens_total = int(rng.choice([0, 0, 1, 2]))
    quotes_total = int(rng.choice([0, 0, 1, 2]))
    longs = int(rng.choice([0, 1, 2, 3]))
    vowels = int(rng.choice([0, 1, 2, 3, 4]))
    p_total = int(rng.choice([0, 0, 2, 4, 5]))
    initial_rule = str(rng.choice(["free", "S", "alpha", "the"]))
    end_long = bool(rng.random() < 0.40)
    caps_sentences = int(rng.choice([0, 1, 1, 2]))
    question_sentences = int(rng.choice([0, 1, 1, 2]))
    ly_sentences = int(rng.choice([0, 0, 1, n_sent]))
    integers = list(_INT_MODES[int(rng.integers(0, len(_INT_MODES)))])
    percents = int(rng.choice([0, 0, 1, 2]))
    forbidden = int(rng.choice([0, 0, 1, 2]))
    required = bool(rng.random() < 0.35)
    neutral = bool(rng.random() < 0.45)
    unique = bool(rng.random() < 0.12)

    if unique:
        # All-words-unique is otherwise unreachable: a deck drawn without
        # replacement is the only way C_W1 ever passes in dry run.
        pool = list(dict.fromkeys(_SHORT + _LONG + _VOWEL + _PWORD + _LY))
        deck = [pool[k] for k in rng.permutation(len(pool))]
        n_sent = min(n_sent, 3)
        lengths = [min(lengths[s], 6) for s in range(n_sent)]
        integers, percents, forbidden, required = [], 0, 0, False
        neutral = False
    else:
        deck = None

    carrier = int(np.argmax(lengths))
    specials: dict[int, list[str]] = {s: [] for s in range(n_sent)}
    specials[carrier].extend(str(v) for v in integers)
    specials[carrier].extend(f"{int(rng.integers(5, 96))}%" for _ in range(percents))
    for k in range(forbidden):
        specials[carrier].append(_FORBIDDEN[k % len(_FORBIDDEN)])
    if required:
        specials[carrier % n_sent].extend(_REQUIRED)
    if neutral:
        specials[carrier].append(CFG.u_neutral_word)

    alphabet = "abcdefghijklmnopqrstuvwxyz"
    out: list[str] = []
    for s in range(n_sent):
        if initial_rule == "S":
            first = "silt"
        elif initial_rule == "alpha":
            first = f"{alphabet[s]}pex" if s else "apex"
        elif initial_rule == "the":
            first = "the"
        else:
            first = None
        tokens = _compose_sentence(
            rng, lengths[s], first=first, longs=longs, vowels=vowels,
            p_words=(p_total if s == carrier else 0),
            specials=specials[s], ly=(s < ly_sentences), caps=(s < caps_sentences),
            deck=deck)
        out.append(_render_sentence(
            tokens, commas=commas,
            semicolons=(1 if semi_each else (1 if s < semi_total else 0)),
            colons=(1 if s < colons_total else 0),
            parens=(1 if s < parens_total else 0),
            quotes=(1 if s < quotes_total else 0),
            question=(s >= n_sent - question_sentences and question_sentences > 0),
            end_long=end_long, rng=rng))
    return " ".join(out)


def _build_synthetic_corpus(n: int = 260) -> list[str]:
    corpus = [_synthetic_variant(i) for i in range(n)]
    corpus.extend([
        "Locks lift boats. Gates hold the water back firmly. Chambers fill "
        "until the levels finally match exactly. Boats then move onward "
        "through the opened upper gates without any further delay today.",
        "An open estimate arrives early. Every autumn an old estimate is "
        "available. Under an inch of open air, estimates arrive early anyway.",
        "yes",
        "It depends.",
    ])
    return [c for c in dict.fromkeys(corpus) if normalize_text(c)]


# Non-evidence pilot outputs for the verifier audit. Real model output breaks
# verifiers in ways authored prose does not: chat preambles, list framing,
# unbalanced brackets, truncation mid-sentence. Populate this from a dev_fast or
# pilot run before signing the audit -- never from a study-profile confirmatory
# run, because repairing a verifier from confirmatory output is repairing the
# measurement after seeing the result.
PILOT_AUDIT_OUTPUTS_PATH = AUDIT_DIR / "pilot_outputs_for_audit.json"
if PILOT_AUDIT_OUTPUTS_PATH.exists():
    PILOT_AUDIT_OUTPUTS = [str(t) for t in json.loads(
        PILOT_AUDIT_OUTPUTS_PATH.read_text())][:400]
    PILOT_AUDIT_SOURCE = f"{PILOT_AUDIT_OUTPUTS_PATH.name} ({len(PILOT_AUDIT_OUTPUTS)} outputs)"
else:
    PILOT_AUDIT_OUTPUTS = []
    PILOT_AUDIT_SOURCE = "absent: the audit sample is authored text only"

SYNTHETIC_CORPUS = _build_synthetic_corpus()
SYNTHETIC_FAIL = pd.DataFrame(
    {cid: [1 - verify(text, cid).binary_pass for text in SYNTHETIC_CORPUS]
     for cid in CONSTRAINTS})
_mean_fail = SYNTHETIC_FAIL.mean(axis=1)
_median = float(_mean_fail.median())
SYN_HARD_IDX = [i for i in range(len(SYNTHETIC_CORPUS)) if _mean_fail[i] > _median]
SYN_EASY_IDX = [i for i in range(len(SYNTHETIC_CORPUS)) if _mean_fail[i] <= _median]

# Draw pools per MEASURED constraint. A split by average difficulty leaves an
# individual constraint pinned in both halves, which is exactly the ceiling
# artefact that makes a dry run uninformative. Splitting on the constraint under
# measurement makes the realised failure rate equal beta by construction, so the
# closed form below is exact rather than approximate.
SYN_VIOLATING = {cid: [i for i in range(len(SYNTHETIC_CORPUS))
                       if SYNTHETIC_FAIL.at[i, cid] == 1] for cid in CONSTRAINTS}
SYN_SATISFYING = {cid: [i for i in range(len(SYNTHETIC_CORPUS))
                        if SYNTHETIC_FAIL.at[i, cid] == 0] for cid in CONSTRAINTS}

SYN_BASE, SYN_SCALE, SYN_PAIR = 0.10, 0.45, 0.10
SYN_ORDER = {"target_first": -0.05, "added_first": 0.05, "isolated": 0.0, "none": 0.0}
SYN_FOCAL_EXCESS = 0.12
SYN_BETA_CEILING = 0.95


def _latent_difficulty(cid: str) -> float:
    """Per-constraint difficulty under the oracle. Dry run only.

    Constraints named in oracle_planted_twins are given the focal constraint's
    difficulty with a small deterministic jitter. Without them the oracle draws
    every difficulty from an independent hash, no candidate resembles the focal
    constraint on any component, and the reference-exists branch of the later
    gates can never execute -- so the dry run would leave the machinery that
    matters most entirely untested.
    """
    base = 0.15 + 0.55 * (stable_int(f"syn|{cid}", 1000) / 1000.0)
    if (CFG.oracle_u_target_latent is not None
            and cid in CONSTRAINTS and CONSTRAINTS[cid].role == "unrelated"):
        return float(CFG.oracle_u_target_latent
                     + 0.04 * (stable_int(f"ulat|{cid}", 100) / 100.0 - 0.5))
    if cid in CFG.oracle_planted_twins and cid != CFG.focal_id:
        focal = 0.15 + 0.55 * (stable_int(f"syn|{CFG.focal_id}", 1000) / 1000.0)
        return focal + CFG.oracle_twin_jitter * (
            stable_int(f"twin|{cid}", 100) / 100.0 - 0.5)
    return base


def synthetic_beta(ordered_ids: list[str], order: str, added: str) -> float:
    """Probability of drawing a response that violates the measured constraint."""
    beta = SYN_BASE + SYN_SCALE * float(np.mean([_latent_difficulty(c) for c in ordered_ids]))
    if len(ordered_ids) > 1:
        beta += SYN_PAIR
    beta += SYN_ORDER.get(order, 0.0)
    if added == CFG.focal_id:
        beta += SYN_FOCAL_EXCESS
    return float(np.clip(beta, 0.0, SYN_BETA_CEILING))


def _oracle_pools(measured: str) -> tuple[list[int], list[int]]:
    """(violating, satisfying) draw pools for the constraint under measurement."""
    violating = SYN_VIOLATING.get(measured) or SYN_HARD_IDX
    satisfying = SYN_SATISFYING.get(measured) or SYN_EASY_IDX
    return violating, satisfying


def synthetic_expected_fail(ordered_ids: list[str], order: str, added: str,
                            measured: str) -> float:
    """Closed-form E[fail] for a design cell under the oracle."""
    beta = synthetic_beta(ordered_ids, order, added)
    violating, satisfying = _oracle_pools(measured)
    hard = float(SYNTHETIC_FAIL.loc[violating, measured].mean())
    easy = float(SYNTHETIC_FAIL.loc[satisfying, measured].mean())
    return beta * hard + (1 - beta) * easy


def synthetic_response(row: dict[str, Any]) -> str:
    ids = row["ordered_constraint_ids"]
    if isinstance(ids, str):
        ids = json.loads(ids)
    beta = synthetic_beta(ids, row.get("order", "none"), row.get("added_constraint", ""))
    measured = str(row.get("measured_constraint") or "") or (ids[0] if ids else "")
    violating, satisfying = _oracle_pools(measured)
    rng = np.random.default_rng(stable_int(f"oracle|{row['row_id']}"))
    pool = violating if rng.random() < beta else satisfying
    return SYNTHETIC_CORPUS[int(rng.choice(pool))]


# ---------------------------------------------------------- batch planning
def build_batch_plan(design: pd.DataFrame) -> list[dict[str, Any]]:
    rows = design.to_dict("records")
    rows.sort(key=lambda r: (r["repetition_seed"], stable_int(r["row_id"]), r["row_id"]))
    plan, size = [], CFG.initial_batch_size
    for index, start in enumerate(range(0, len(rows), size)):
        members = [r["row_id"] for r in rows[start:start + size]]
        plan.append({"batch_index": index,
                     "batch_seed": CFG.base_seed + stable_int("|".join(members), 1_000_000),
                     "row_ids": members})
    return plan


def load_or_create_batch_plan(design: pd.DataFrame, stage: str) -> list[dict[str, Any]]:
    plan = build_batch_plan(design)
    digest = sha(plan)
    path = DESIGN_DIR / f"{stage}_batch_plan.json"
    if path.exists():
        stored = json.loads(path.read_text())
        if stored.get("plan_sha256") != digest:
            raise FrozenPlanMismatch(
                f"the frozen batch plan for stage {stage} does not match the "
                f"plan the current design produces.\n  stored:  {stored.get('plan_sha256')}\n"
                f"  current: {digest}\nA different plan is a different "
                "randomisation. Escalation must open a NEW stage name rather "
                "than reopening this one.")
        return stored["batches"]
    durable_write(path, json.dumps(
        {"stage": stage, "plan_sha256": digest, "batch_size": CFG.initial_batch_size,
         "n_batches": len(plan), "batches": plan}, indent=2))
    return plan


def rows_for_design(design: pd.DataFrame, stage: str, plan: list[dict[str, Any]],
                    require_complete: bool = True) -> pd.DataFrame:
    """Join cached payload onto the authoritative design.

    The journal stores only generated output. Design metadata is never read
    back from it, so a malformed record cannot carry an inconsistent
    condition_id, task_id or constraint list into verification.
    """
    payload, audit = read_commits(stage, plan)
    wanted = set(design["row_id"])
    if audit["duplicate"]:
        raise CacheIntegrityError(
            f"{audit['duplicate']} duplicate row_ids across committed batches "
            f"in stage {stage}.")

    verified = {}
    prompt_by_id = {r["row_id"]: r["user_prompt"] for r in design.to_dict("records")}
    mismatched = rendered_mismatch = 0
    for rid, record in payload.items():
        if rid not in wanted:
            continue
        if record.get("prompt_sha256") != prompt_fingerprint(prompt_by_id[rid]):
            mismatched += 1
            continue
        expected = TOKENISATION_MANIFEST.get(rid)
        if expected and record.get("rendered_sha256") not in (
                None, expected["rendered_sha256"]):
            rendered_mismatch += 1
            continue
        verified[rid] = record
    if mismatched:
        raise CacheIntegrityError(
            f"{mismatched} committed rows in stage {stage} were generated from "
            "a different prompt than the current design renders.")
    if rendered_mismatch:
        raise CacheIntegrityError(
            f"{rendered_mismatch} committed rows in stage {stage} were "
            "generated from a different rendered chat template.")

    missing = wanted - set(verified)
    if require_complete and missing:
        raise CacheIntegrityError(
            f"{len(missing)} design rows are absent from the committed journal "
            f"for stage {stage}.")

    frame = design.copy()
    for column, default in (("response_text", ""), ("generation_ok", False),
                            ("generation_error", None), ("batch_seed", np.nan),
                            ("batch_index", np.nan), ("plan_deviation", False),
                            ("is_synthetic", False)):
        frame[column] = [verified.get(r, {}).get(column, default)
                         for r in frame["row_id"]]
    frame["model_id"] = CFG.model_id
    frame["model_revision"] = CFG.model_revision
    frame["model_profile"] = CFG.model_profile
    CACHE_STATS.setdefault(stage, {}).update(audit)
    return frame


# ----------------------------------------------------------- prompt cache
_PROMPT_TEXT: dict[str, str] = {}
_PROMPT_IDS: dict[str, list[int]] = {}
TOKENISATION_MANIFEST: dict[str, dict[str, Any]] = {}
_PROMPT_MODE: Optional[str] = None


def prerender_prompts(design: pd.DataFrame) -> None:
    """Render and tokenise once, then prove parity with the per-batch call."""
    global _PROMPT_MODE

    if not CFG.dry_run:
        load_model()
    if tokenizer is None and not CFG.dry_run:
        raise RuntimeError("prerender_prompts requires a loaded tokenizer.")

    mode = "synthetic" if CFG.dry_run else "chat_template"
    if _PROMPT_MODE is not None and _PROMPT_MODE != mode:
        _PROMPT_TEXT.clear()
        _PROMPT_IDS.clear()
        TOKENISATION_MANIFEST.clear()
        print(f"prompt cache cleared: render mode changed {_PROMPT_MODE} -> {mode}")
    _PROMPT_MODE = mode

    with phase("prerender"):
        rows = design.to_dict("records")
        for row in rows:
            if row["row_id"] in _PROMPT_TEXT:
                continue
            if CFG.dry_run:
                _PROMPT_TEXT[row["row_id"]] = row["user_prompt"]
                continue
            _PROMPT_TEXT[row["row_id"]] = tokenizer.apply_chat_template(
                [{"role": "system", "content": SYSTEM_MESSAGE},
                 {"role": "user", "content": row["user_prompt"]}],
                tokenize=False, add_generation_prompt=True)
        if CFG.dry_run:
            return

        pending = [r["row_id"] for r in rows if r["row_id"] not in _PROMPT_IDS]
        if not pending:
            return
        # Tokenise WITHOUT truncation first, so the true length is known before
        # anything is cut. v14 tokenised with truncation=True and then recorded
        # "truncated" as a diagnostic, which means a scientific prompt whose
        # instruction block was cut off could still be generated: the model
        # would be answering a different question from the one in the design.
        untruncated = tokenizer([_PROMPT_TEXT[r] for r in pending],
                                add_special_tokens=False,
                                truncation=False)["input_ids"]
        _FULL_PROMPT_LENGTH.update(
            {r: len(ids) for r, ids in zip(pending, untruncated)})
        limit = CFG.max_input_tokens - CFG.input_token_headroom
        over = [(r, len(ids)) for r, ids in zip(pending, untruncated) if len(ids) > limit]
        if over and CFG.forbid_input_truncation:
            offending = pd.DataFrame(over, columns=["row_id", "input_tokens"])
            offending["limit"] = limit
            offending.to_csv(RUN_ROOT / "input_truncation_offenders.csv", index=False)
            display(offending.head(20))
            stop("generation", GateStatus.INPUT_TRUNCATION,
                 f"{len(over)} scientific prompts exceed the declared input cap",
                 quantities={"n_offending": len(over),
                             "longest": int(max(n for _, n in over)),
                             "limit": limit,
                             "examples": [r for r, _ in over[:10]]},
                 thresholds={"max_input_tokens": CFG.max_input_tokens,
                             "headroom": CFG.input_token_headroom},
                 more_data_could_resolve=False, new_protocol_version_required=True,
                 message=f"""
INPUT_TRUNCATION: {len(over)} prompts do not fit inside max_input_tokens.

The longest is {int(max(n for _, n in over))} tokens against a cap of {limit}. Generating them would
answer a silently different question from the one the design specifies, and no
downstream analysis can detect that. The offending rows are listed in
input_truncation_offenders.csv.

Raising max_input_tokens is legitimate and changes the execution condition, so
it changes the fingerprint and invalidates existing caches. Shortening the task
prompts changes the task bank and its hash. Either is a prospective decision.
Neither is a post-hoc adjustment.
""")
        reference = tokenizer([_PROMPT_TEXT[r] for r in pending],
                              add_special_tokens=False, truncation=True,
                              max_length=CFG.max_input_tokens)["input_ids"]
        _PROMPT_IDS.update(dict(zip(pending, reference)))

        for rid in pending:
            rendered = _PROMPT_TEXT[rid]
            check = tokenizer(rendered, add_special_tokens=False, truncation=True,
                              max_length=CFG.max_input_tokens)["input_ids"]
            if check != _PROMPT_IDS[rid]:
                raise RuntimeError(
                    f"tokenisation parity failed for {rid}: batched and single "
                    "tokenisation of the same rendered template differ.")
            with_special = tokenizer(rendered, add_special_tokens=True,
                                     truncation=True,
                                     max_length=CFG.max_input_tokens)["input_ids"]
            if with_special != _PROMPT_IDS[rid]:
                raise RuntimeError(
                    "add_special_tokens changes the token ids for this "
                    f"tokenizer on {rid}. The chat template already carries the "
                    "special tokens, so this must be decided deliberately.")
            TOKENISATION_MANIFEST[rid] = {
                "rendered_sha256": sha_text(rendered),
                "add_special_tokens_equivalent": True,
                "token_ids_sha256": sha_text(json.dumps(_PROMPT_IDS[rid])),
                "input_length": len(_PROMPT_IDS[rid]),
                "full_input_length": _FULL_PROMPT_LENGTH.get(rid, len(_PROMPT_IDS[rid])),
                "truncated": _FULL_PROMPT_LENGTH.get(rid, 0) > CFG.max_input_tokens}
        truncated = sum(v["truncated"] for v in TOKENISATION_MANIFEST.values())
        print(f"tokenisation parity verified for {len(pending)} prompts; "
              f"{truncated} truncated at max_input_tokens")
        durable_write(CONFIG_DIR / "tokenisation_manifest.json",
                      json.dumps(TOKENISATION_MANIFEST, indent=2))


# Per-row termination diagnostics for every generated row, of every stage.
TERMINATION_RECORDS: list[dict[str, Any]] = []
_FULL_PROMPT_LENGTH: dict[str, int] = {}


def generate_batch(batch_rows: list[dict[str, Any]],
                   batch_seed: int) -> tuple[list[str], dict[str, Any]]:
    profile: dict[str, Any] = {}
    if CFG.dry_run:
        texts = [synthetic_response(r) for r in batch_rows]
        for r, text in zip(batch_rows, texts):
            tokens = len(word_tokens(text))
            TERMINATION_RECORDS.append({
                "row_id": r["row_id"], "generated_token_count": tokens,
                "ended_with_eos": True, "hit_max_new_tokens": False,
                "output_truncated": False, "stop_reason": "synthetic_eos"})
        return texts, profile

    load_model()
    set_all_seeds(batch_seed)

    absent = [r["row_id"] for r in batch_rows if r["row_id"] not in _PROMPT_IDS]
    if absent:
        raise RuntimeError(f"{len(absent)} rows were never pre-tokenised.")

    t0 = time.perf_counter()
    padded = tokenizer.pad({"input_ids": [_PROMPT_IDS[r["row_id"]] for r in batch_rows]},
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
            temperature=CFG.temperature, top_p=CFG.top_p,
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
    TERMINATION_RECORDS.extend(terminations)
    profile["output_tokens"] = int(sum(lengths))
    profile["n_hit_max_new_tokens"] = int(sum(t["hit_max_new_tokens"] for t in terminations))
    profile["peak_allocated_bytes"] = int(torch.cuda.max_memory_allocated())
    profile["peak_reserved_bytes"] = int(torch.cuda.max_memory_reserved())

    t0 = time.perf_counter()
    texts = tokenizer.batch_decode(generated, skip_special_tokens=True)
    profile["decode_seconds"] = time.perf_counter() - t0
    return texts, profile


def run_generation_stage(design: pd.DataFrame,
                         stage_name: Optional[str] = None) -> pd.DataFrame:
    """Restore from the durable mirror first, then generate only what is missing."""
    stage = stage_name or design["stage"].iloc[0]
    plan = load_or_create_batch_plan(design, stage)
    profile_path = RUN_ROOT / f"{stage}_batch_profile.jsonl"

    restored = restore_from_drive(stage, plan)
    if restored["restored"] or restored["quarantined"]:
        print(f"[{stage}] restored {restored['restored']} batches "
              f"({restored['rows_restored']} rows) from the durable mirror; "
              f"{restored['quarantined']} quarantined; "
              f"{restored['already_local']} already local.")

    payload, _ = read_commits(stage, plan)
    complete = set(payload)
    pending = [b for b in plan if not set(b["row_ids"]).issubset(complete)]
    served = len(set(design["row_id"]) & complete)
    print(f"[{stage}] {served}/{len(design)} rows committed; "
          f"{len(pending)} of {len(plan)} planned batches to run.")

    if served and CFG.require_fresh_generation:
        raise RuntimeError(f"{served} {stage} rows resumed while "
                           "require_fresh_generation is set.")

    if pending:
        prerender_prompts(design)
        by_id = {r["row_id"]: r for r in design.to_dict("records")}
        progress = tqdm(total=sum(len(b["row_ids"]) for b in pending), desc=stage)
        with phase(f"generate_{stage}"):
            for planned in pending:
                queue, attempt = [(planned["row_ids"], planned["batch_seed"], 0)], 0
                while queue:
                    member_ids, seed, depth = queue.pop(0)
                    rows = [by_id[r] for r in member_ids]
                    started = time.perf_counter()
                    try:
                        texts, prof = generate_batch(rows, seed)
                    except torch.cuda.OutOfMemoryError as exc:
                        gc.collect()
                        torch.cuda.empty_cache()
                        if CFG.adaptive_batching == "off":
                            raise RuntimeError(
                                f"CUDA OOM on {stage} batch {planned['batch_index']} "
                                f"of size {len(member_ids)}. The run stops here "
                                "deliberately: splitting the batch would change "
                                "batch membership and therefore the sample. The "
                                "frozen plan and every committed batch are "
                                "reusable, and the durable mirror means resuming "
                                "costs only the batch in flight.") from exc
                        if len(member_ids) > 1:
                            half = len(member_ids) // 2
                            left, right = member_ids[:half], member_ids[half:]
                            queue = [
                                (left, CFG.base_seed + stable_int("|".join(left), 1_000_000),
                                 depth + 1),
                                (right, CFG.base_seed + stable_int("|".join(right), 1_000_000),
                                 depth + 1)] + queue
                            continue
                        texts, prof = None, {}

                    if texts is None:
                        records = [{"row_id": rows[0]["row_id"], "response_text": "",
                                    "generation_ok": False,
                                    "generation_error": "CUDA OOM at batch size 1"}]
                    else:
                        records = [{"row_id": row["row_id"], "response_text": text.strip(),
                                    "generation_ok": True, "generation_error": None}
                                   for row, text in zip(rows, texts)]

                    for record, row in zip(records, rows):
                        tok = TOKENISATION_MANIFEST.get(row["row_id"], {})
                        record.update({
                            "prompt_sha256": prompt_fingerprint(row["user_prompt"]),
                            "rendered_sha256": tok.get("rendered_sha256"),
                            "token_ids_sha256": tok.get("token_ids_sha256"),
                            "is_synthetic": CFG.dry_run,
                            "model_profile": CFG.model_profile,
                            "batch_seed": seed, "batch_index": planned["batch_index"],
                            "plan_deviation": depth > 0,
                            "run_attempt_id": RUN_ATTEMPT_ID})

                    if depth > 0:
                        log_departure(
                            "generation",
                            f"{stage} batch {planned['batch_index']} under the frozen plan",
                            f"generated after an OOM split into {len(member_ids)} rows",
                            "adaptive_batching is 'exploratory'; these rows are "
                            "not confirmatory evidence")

                    commit_batch(stage, planned["batch_index"], attempt, records, {
                        "planned_batch_index": planned["batch_index"],
                        "row_ids_planned": planned["row_ids"],
                        "row_ids_realised": member_ids, "batch_seed": seed,
                        "realised_batch_size": len(member_ids),
                        "plan_deviation": depth > 0,
                        "run_attempt_id": RUN_ATTEMPT_ID})
                    attempt += 1

                    with profile_path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({
                            "run_attempt_id": RUN_ATTEMPT_ID,
                            "execution_sha256": EXECUTION_SHA256,
                            "model_profile": CFG.model_profile,
                            "stage": stage, "batch_index": planned["batch_index"],
                            "batch_seed": seed, "split_depth": depth,
                            "batch_size": len(member_ids),
                            "started_utc": datetime.now(timezone.utc).isoformat(),
                            "wall_seconds": time.perf_counter() - started,
                            "gpu_name": (torch.cuda.get_device_name()
                                         if torch.cuda.is_available() else None),
                            **prof}) + "\n")
                    progress.update(len(member_ids))
        progress.close()

    return rows_for_design(design, stage, plan)


def report_batch_composition(responses: pd.DataFrame, label: str) -> pd.DataFrame:
    table = pd.crosstab(responses["condition_id"], responses["batch_seed"])
    per_condition = (table > 0).sum(axis=1).rename("distinct_batches")
    single = per_condition[per_condition == 1]
    if not single.empty:
        print(f"WARNING [{label}]: single-batch conditions: {list(single.index)[:8]}")
    return per_condition.to_frame()


def batch_profile_summary(stage: str) -> pd.DataFrame:
    records = [r for r in load_jsonl(RUN_ROOT / f"{stage}_batch_profile.jsonl")
               if r.get("run_attempt_id") == RUN_ATTEMPT_ID]
    if not records:
        return pd.DataFrame([{"stage": stage, "batches_this_attempt": 0}])
    df = pd.DataFrame(records)
    gen = float(df.get("generate_seconds", pd.Series([np.nan])).sum())
    out = {"stage": stage, "run_attempt_id": RUN_ATTEMPT_ID,
           "batches_this_attempt": len(df), "rows": int(df["batch_size"].sum()),
           "wall_seconds": float(df["wall_seconds"].sum()),
           "generate_seconds": gen,
           "input_tokens": int(df.get("input_tokens", pd.Series([0])).sum()),
           "output_tokens": int(df.get("output_tokens", pd.Series([0])).sum()),
           "splits": int(df["split_depth"].gt(0).sum())}
    out["output_tokens_per_second"] = out["output_tokens"] / gen if gen else np.nan
    return pd.DataFrame([out])


def score_responses(responses: pd.DataFrame) -> pd.DataFrame:
    """Verify every constraint present in each response."""
    rows = []
    _TERMINATION_BY_ROW = {t["row_id"]: t for t in TERMINATION_RECORDS}
    with phase("verify"):
        for r in responses.to_dict("records"):
            ids = r["ordered_constraint_ids"]
            if isinstance(ids, str):
                ids = json.loads(ids)
            term = _TERMINATION_BY_ROW.get(r.get("row_id"), {})
            for cid in ids:
                if r.get("generation_ok", False):
                    res = verify(r.get("response_text", ""), cid)
                else:
                    res = VerificationResult("unscorable", 0, 0.0,
                                             {"generation_error": r.get("generation_error")})
                rows.append({
                    "row_id": r["row_id"], "stage": r["stage"], "task_id": r["task_id"],
                    "condition_id": r["condition_id"],
                    "added_constraint": r["added_constraint"],
                    "measured_constraint": r.get("measured_constraint", ""),
                    "is_measured": cid == r.get("measured_constraint", ""),
                    "order": r["order"], "paraphrase_id": r["paraphrase_id"],
                    "repetition_seed": r["repetition_seed"], "constraint_id": cid,
                    "generative_scope": CONSTRAINTS[cid].generative_scope,
                    "status": res.status, "binary_pass": res.binary_pass,
                    "fail": 1 - res.binary_pass,
                    "continuous_score": res.continuous_score,
                    "detail_json": json.dumps(res.detail, ensure_ascii=False),
                    "generation_ok": bool(r.get("generation_ok", False)),
                    "plan_deviation": bool(r.get("plan_deviation", False)),
                    "is_synthetic": bool(r.get("is_synthetic", False)),
                    "model_profile": CFG.model_profile,
                    "response_words": len(word_tokens(r.get("response_text", ""))),
                    **{k: term.get(k) for k in
                       ("generated_token_count", "ended_with_eos",
                        "hit_max_new_tokens", "output_truncated", "stop_reason")},
                })
    return pd.DataFrame(rows)


def termination_frame() -> pd.DataFrame:
    return indexed_frame(
        list({t["row_id"]: t for t in TERMINATION_RECORDS}.values()), "row_id",
        ["row_id", "generated_token_count", "ended_with_eos",
         "hit_max_new_tokens", "output_truncated", "stop_reason"])


def output_cap_report(scored: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Truncation and termination by arm. Post-treatment, reported not adjusted.

    Conditioning the primary estimate on successful termination would condition
    on an outcome of the treatment, so these never enter tau. They are here to
    detect the case where the declared output cap, rather than the constraint,
    is what the study is measuring.
    """
    present = [c for c in by if c in scored.columns]
    if not present or "output_truncated" not in scored.columns:
        return pd.DataFrame()
    grouped = scored.groupby(present, dropna=False).agg(
        n=("row_id", "size"),
        truncated_share=("output_truncated", "mean"),
        hit_cap_share=("hit_max_new_tokens", "mean"),
        eos_share=("ended_with_eos", "mean"),
        mean_generated_tokens=("generated_token_count", "mean"))
    return grouped.reset_index()


print(f"synthetic corpus: {len(SYNTHETIC_CORPUS)} responses "
      f"({len(SYN_EASY_IDX)} easy, {len(SYN_HARD_IDX)} hard)")
print(f"designed focal excess {SYN_FOCAL_EXCESS:+.2f}, order effect "
      f"{SYN_ORDER['added_first'] - SYN_ORDER['target_first']:+.2f} on the beta scale")
