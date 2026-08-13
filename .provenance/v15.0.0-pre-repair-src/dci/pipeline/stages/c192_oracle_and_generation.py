"""Stage 192 — migrated from notebook cell 192.py (oracle_and_generation).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/192.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import indexed_frame  # noqa: F401
from dci.exceptions import CacheIntegrityError, FrozenPlanMismatch  # noqa: F401
from dci.provenance.hashes import sha, sha_text, stable_int  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401
from dci.verifiers.rules import VerificationResult, normalize_text, word_tokens  # noqa: F401

from dci.pipeline.sharding import shard_filter, wait_for_stage_complete


def prompt_fingerprint(user_prompt: str) -> str:
    """Tokenizer-free identity of the text sent to the model."""
    return sha_text(S.SYSTEM_MESSAGE + "\x00" + user_prompt)
S.prompt_fingerprint = prompt_fingerprint


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
_FORBIDDEN = list(S.CFG.u_forbidden_words)
_REQUIRED = list(S.CFG.u_required_words)
_LONG_LETTERS = S.CFG.long_word_letters

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
        specials[carrier].append(S.CFG.u_neutral_word)

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
PILOT_AUDIT_OUTPUTS_PATH = S.AUDIT_DIR / "pilot_outputs_for_audit.json"
if PILOT_AUDIT_OUTPUTS_PATH.exists():
    S.PILOT_AUDIT_OUTPUTS = [str(t) for t in json.loads(
        PILOT_AUDIT_OUTPUTS_PATH.read_text())][:400]
    S.PILOT_AUDIT_SOURCE = f"{PILOT_AUDIT_OUTPUTS_PATH.name} ({len(S.PILOT_AUDIT_OUTPUTS)} outputs)"
else:
    S.PILOT_AUDIT_OUTPUTS = []
    S.PILOT_AUDIT_SOURCE = "absent: the audit sample is authored text only"

S.SYNTHETIC_CORPUS = _build_synthetic_corpus()
S.SYNTHETIC_FAIL = pd.DataFrame(
    {cid: [1 - S.verify(text, cid).binary_pass for text in S.SYNTHETIC_CORPUS]
     for cid in S.CONSTRAINTS})
_mean_fail = S.SYNTHETIC_FAIL.mean(axis=1)
_median = float(_mean_fail.median())
SYN_HARD_IDX = [i for i in range(len(S.SYNTHETIC_CORPUS)) if _mean_fail[i] > _median]
SYN_EASY_IDX = [i for i in range(len(S.SYNTHETIC_CORPUS)) if _mean_fail[i] <= _median]

# Draw pools per MEASURED constraint. A split by average difficulty leaves an
# individual constraint pinned in both halves, which is exactly the ceiling
# artefact that makes a dry run uninformative. Splitting on the constraint under
# measurement makes the realised failure rate equal beta by construction, so the
# closed form below is exact rather than approximate.
S.SYN_VIOLATING = {cid: [i for i in range(len(S.SYNTHETIC_CORPUS))
                       if S.SYNTHETIC_FAIL.at[i, cid] == 1] for cid in S.CONSTRAINTS}
S.SYN_SATISFYING = {cid: [i for i in range(len(S.SYNTHETIC_CORPUS))
                        if S.SYNTHETIC_FAIL.at[i, cid] == 0] for cid in S.CONSTRAINTS}

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
    if (S.CFG.oracle_u_target_latent is not None
            and cid in S.CONSTRAINTS and S.CONSTRAINTS[cid].role == "unrelated"):
        return float(S.CFG.oracle_u_target_latent
                     + 0.04 * (stable_int(f"ulat|{cid}", 100) / 100.0 - 0.5))
    if cid in S.CFG.oracle_planted_twins and cid != S.CFG.focal_id:
        focal = 0.15 + 0.55 * (stable_int(f"syn|{S.CFG.focal_id}", 1000) / 1000.0)
        return focal + S.CFG.oracle_twin_jitter * (
            stable_int(f"twin|{cid}", 100) / 100.0 - 0.5)
    return base


def synthetic_beta(ordered_ids: list[str], order: str, added: str) -> float:
    """Probability of drawing a response that violates the measured constraint."""
    beta = SYN_BASE + SYN_SCALE * float(np.mean([_latent_difficulty(c) for c in ordered_ids]))
    if len(ordered_ids) > 1:
        beta += SYN_PAIR
    beta += SYN_ORDER.get(order, 0.0)
    if added == S.CFG.focal_id:
        beta += SYN_FOCAL_EXCESS
    return float(np.clip(beta, 0.0, SYN_BETA_CEILING))
S.synthetic_beta = synthetic_beta


def _oracle_pools(measured: str) -> tuple[list[int], list[int]]:
    """(violating, satisfying) draw pools for the constraint under measurement."""
    violating = S.SYN_VIOLATING.get(measured) or SYN_HARD_IDX
    satisfying = S.SYN_SATISFYING.get(measured) or SYN_EASY_IDX
    return violating, satisfying


def synthetic_expected_fail(ordered_ids: list[str], order: str, added: str,
                            measured: str) -> float:
    """Closed-form E[fail] for a design cell under the oracle."""
    beta = S.synthetic_beta(ordered_ids, order, added)
    violating, satisfying = _oracle_pools(measured)
    hard = float(S.SYNTHETIC_FAIL.loc[violating, measured].mean())
    easy = float(S.SYNTHETIC_FAIL.loc[satisfying, measured].mean())
    return beta * hard + (1 - beta) * easy
S.synthetic_expected_fail = synthetic_expected_fail


def synthetic_response(row: dict[str, Any]) -> str:
    ids = row["ordered_constraint_ids"]
    if isinstance(ids, str):
        ids = json.loads(ids)
    beta = S.synthetic_beta(ids, row.get("order", "none"), row.get("added_constraint", ""))
    measured = str(row.get("measured_constraint") or "") or (ids[0] if ids else "")
    violating, satisfying = _oracle_pools(measured)
    rng = np.random.default_rng(stable_int(f"oracle|{row['row_id']}"))
    pool = violating if rng.random() < beta else satisfying
    return S.SYNTHETIC_CORPUS[int(rng.choice(pool))]
S.synthetic_response = synthetic_response


# ---------------------------------------------------------- batch planning
def build_batch_plan(design: pd.DataFrame) -> list[dict[str, Any]]:
    rows = design.to_dict("records")
    rows.sort(key=lambda r: (r["repetition_seed"], stable_int(r["row_id"]), r["row_id"]))
    plan, size = [], S.CFG.initial_batch_size
    for index, start in enumerate(range(0, len(rows), size)):
        members = [r["row_id"] for r in rows[start:start + size]]
        plan.append({"batch_index": index,
                     "batch_seed": S.CFG.base_seed + stable_int("|".join(members), 1_000_000),
                     "row_ids": members})
    return plan
S.build_batch_plan = build_batch_plan


def load_or_create_batch_plan(design: pd.DataFrame, stage: str) -> list[dict[str, Any]]:
    plan = S.build_batch_plan(design)
    digest = sha(plan)
    path = S.DESIGN_DIR / f"{stage}_batch_plan.json"
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
    S.durable_write(path, json.dumps(
        {"stage": stage, "plan_sha256": digest, "batch_size": S.CFG.initial_batch_size,
         "n_batches": len(plan), "batches": plan}, indent=2))
    return plan


def rows_for_design(design: pd.DataFrame, stage: str, plan: list[dict[str, Any]],
                    require_complete: bool = True) -> pd.DataFrame:
    """Join cached payload onto the authoritative design.

    The journal stores only generated output. Design metadata is never read
    back from it, so a malformed record cannot carry an inconsistent
    condition_id, task_id or constraint list into verification.
    """
    payload, audit = S.read_commits(stage, plan)
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
        if record.get("prompt_sha256") != S.prompt_fingerprint(prompt_by_id[rid]):
            mismatched += 1
            continue
        expected = S.TOKENISATION_MANIFEST.get(rid)
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
    frame["model_id"] = S.CFG.model_id
    frame["model_revision"] = S.CFG.model_revision
    frame["model_profile"] = S.CFG.model_profile
    S.CACHE_STATS.setdefault(stage, {}).update(audit)
    return frame


# ----------------------------------------------------------- prompt cache
S._PROMPT_TEXT: dict[str, str] = {}
S._PROMPT_IDS: dict[str, list[int]] = {}
S.TOKENISATION_MANIFEST: dict[str, dict[str, Any]] = {}
S._PROMPT_MODE: Optional[str] = None


def prerender_prompts(design: pd.DataFrame) -> None:
    """Render and tokenise once, then prove parity with the per-batch call."""
    pass

    if not S.CFG.dry_run:
        S.load_model()
    if S.tokenizer is None and not S.CFG.dry_run:
        raise RuntimeError("prerender_prompts requires a loaded tokenizer.")

    mode = "synthetic" if S.CFG.dry_run else "chat_template"
    if S._PROMPT_MODE is not None and S._PROMPT_MODE != mode:
        S._PROMPT_TEXT.clear()
        S._PROMPT_IDS.clear()
        S.TOKENISATION_MANIFEST.clear()
        print(f"prompt cache cleared: render mode changed {S._PROMPT_MODE} -> {mode}")
    S._PROMPT_MODE = mode

    with S.phase("prerender"):
        rows = design.to_dict("records")
        for row in rows:
            if row["row_id"] in S._PROMPT_TEXT:
                continue
            if S.CFG.dry_run:
                S._PROMPT_TEXT[row["row_id"]] = row["user_prompt"]
                continue
            S._PROMPT_TEXT[row["row_id"]] = S.tokenizer.apply_chat_template(
                [{"role": "system", "content": S.SYSTEM_MESSAGE},
                 {"role": "user", "content": row["user_prompt"]}],
                tokenize=False, add_generation_prompt=True)
        if S.CFG.dry_run:
            return

        pending = [r["row_id"] for r in rows if r["row_id"] not in S._PROMPT_IDS]
        if not pending:
            return
        # Tokenise WITHOUT truncation first, so the true length is known before
        # anything is cut. v14 tokenised with truncation=True and then recorded
        # "truncated" as a diagnostic, which means a scientific prompt whose
        # instruction block was cut off could still be generated: the model
        # would be answering a different question from the one in the design.
        untruncated = S.tokenizer([S._PROMPT_TEXT[r] for r in pending],
                                add_special_tokens=False,
                                truncation=False)["input_ids"]
        S._FULL_PROMPT_LENGTH.update(
            {r: len(ids) for r, ids in zip(pending, untruncated)})
        limit = S.CFG.max_input_tokens - S.CFG.input_token_headroom
        over = [(r, len(ids)) for r, ids in zip(pending, untruncated) if len(ids) > limit]
        if over and S.CFG.forbid_input_truncation:
            offending = pd.DataFrame(over, columns=["row_id", "input_tokens"])
            offending["limit"] = limit
            offending.to_csv(S.RUN_ROOT / "input_truncation_offenders.csv", index=False)
            display(offending.head(20))
            S.stop("generation", GateStatus.INPUT_TRUNCATION,
                 f"{len(over)} scientific prompts exceed the declared input cap",
                 quantities={"n_offending": len(over),
                             "longest": int(max(n for _, n in over)),
                             "limit": limit,
                             "examples": [r for r, _ in over[:10]]},
                 thresholds={"max_input_tokens": S.CFG.max_input_tokens,
                             "headroom": S.CFG.input_token_headroom},
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
        reference = S.tokenizer([S._PROMPT_TEXT[r] for r in pending],
                              add_special_tokens=False, truncation=True,
                              max_length=S.CFG.max_input_tokens)["input_ids"]
        S._PROMPT_IDS.update(dict(zip(pending, reference)))

        for rid in pending:
            rendered = S._PROMPT_TEXT[rid]
            check = S.tokenizer(rendered, add_special_tokens=False, truncation=True,
                              max_length=S.CFG.max_input_tokens)["input_ids"]
            if check != S._PROMPT_IDS[rid]:
                raise RuntimeError(
                    f"tokenisation parity failed for {rid}: batched and single "
                    "tokenisation of the same rendered template differ.")
            with_special = S.tokenizer(rendered, add_special_tokens=True,
                                     truncation=True,
                                     max_length=S.CFG.max_input_tokens)["input_ids"]
            if with_special != S._PROMPT_IDS[rid]:
                raise RuntimeError(
                    "add_special_tokens changes the token ids for this "
                    f"tokenizer on {rid}. The chat template already carries the "
                    "special tokens, so this must be decided deliberately.")
            S.TOKENISATION_MANIFEST[rid] = {
                "rendered_sha256": sha_text(rendered),
                "add_special_tokens_equivalent": True,
                "token_ids_sha256": sha_text(json.dumps(S._PROMPT_IDS[rid])),
                "input_length": len(S._PROMPT_IDS[rid]),
                "full_input_length": S._FULL_PROMPT_LENGTH.get(rid, len(S._PROMPT_IDS[rid])),
                "truncated": S._FULL_PROMPT_LENGTH.get(rid, 0) > S.CFG.max_input_tokens}
        truncated = sum(v["truncated"] for v in S.TOKENISATION_MANIFEST.values())
        print(f"tokenisation parity verified for {len(pending)} prompts; "
              f"{truncated} truncated at max_input_tokens")
        S.durable_write(S.CONFIG_DIR / "tokenisation_manifest.json",
                      json.dumps(S.TOKENISATION_MANIFEST, indent=2))
S.prerender_prompts = prerender_prompts


# Per-row termination diagnostics for every generated row, of every stage.
S.TERMINATION_RECORDS: list[dict[str, Any]] = []
S._FULL_PROMPT_LENGTH: dict[str, int] = {}


def generate_batch(batch_rows: list[dict[str, Any]],
                   batch_seed: int) -> tuple[list[str], dict[str, Any]]:
    """Delegates to the frozen backend (ledger P7). The oracle branch and the
    torch branch moved verbatim to dci.inference.oracle / .hf_transformers;
    the recorded engine, seeds, decoding and termination metadata are theirs
    to preserve and the execution fingerprint pins which one ran."""
    return S.BACKEND.generate(batch_rows, batch_seed)


def run_generation_stage(design: pd.DataFrame,
                         stage_name: Optional[str] = None) -> pd.DataFrame:
    """Restore from the durable mirror first, then generate only what is missing."""
    stage = stage_name or design["stage"].iloc[0]
    plan = load_or_create_batch_plan(design, stage)
    profile_path = S.RUN_ROOT / f"{stage}_batch_profile.jsonl"

    restored = S.restore_from_drive(stage, plan)
    if restored["restored"] or restored["quarantined"]:
        print(f"[{stage}] restored {restored['restored']} batches "
              f"({restored['rows_restored']} rows) from the durable mirror; "
              f"{restored['quarantined']} quarantined; "
              f"{restored['already_local']} already local.")

    payload, _ = S.read_commits(stage, plan)
    complete = set(payload)
    pending = [b for b in plan if not set(b["row_ids"]).issubset(complete)]
    pending = shard_filter(stage, plan, pending)
    served = len(set(design["row_id"]) & complete)
    print(f"[{stage}] {served}/{len(design)} rows committed; "
          f"{len(pending)} of {len(plan)} planned batches to run.")

    if served and S.CFG.require_fresh_generation:
        raise RuntimeError(f"{served} {stage} rows resumed while "
                           "require_fresh_generation is set.")

    if pending:
        S.prerender_prompts(design)
        by_id = {r["row_id"]: r for r in design.to_dict("records")}
        progress = tqdm(total=sum(len(b["row_ids"]) for b in pending), desc=stage)
        with S.phase(f"generate_{stage}"):
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
                        if S.CFG.adaptive_batching == "off":
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
                                (left, S.CFG.base_seed + stable_int("|".join(left), 1_000_000),
                                 depth + 1),
                                (right, S.CFG.base_seed + stable_int("|".join(right), 1_000_000),
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
                        tok = S.TOKENISATION_MANIFEST.get(row["row_id"], {})
                        record.update({
                            "prompt_sha256": S.prompt_fingerprint(row["user_prompt"]),
                            "rendered_sha256": tok.get("rendered_sha256"),
                            "token_ids_sha256": tok.get("token_ids_sha256"),
                            "is_synthetic": S.CFG.dry_run,
                            "model_profile": S.CFG.model_profile,
                            "batch_seed": seed, "batch_index": planned["batch_index"],
                            "plan_deviation": depth > 0,
                            "run_attempt_id": S.RUN_ATTEMPT_ID})

                    if depth > 0:
                        S.log_departure(
                            "generation",
                            f"{stage} batch {planned['batch_index']} under the frozen plan",
                            f"generated after an OOM split into {len(member_ids)} rows",
                            "adaptive_batching is 'exploratory'; these rows are "
                            "not confirmatory evidence")

                    S.commit_batch(stage, planned["batch_index"], attempt, records, {
                        "planned_batch_index": planned["batch_index"],
                        "row_ids_planned": planned["row_ids"],
                        "row_ids_realised": member_ids, "batch_seed": seed,
                        "realised_batch_size": len(member_ids),
                        "plan_deviation": depth > 0,
                        "run_attempt_id": S.RUN_ATTEMPT_ID})
                    attempt += 1

                    with profile_path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({
                            "run_attempt_id": S.RUN_ATTEMPT_ID,
                            "execution_sha256": S.EXECUTION_SHA256,
                            "model_profile": S.CFG.model_profile,
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

    wait_for_stage_complete(stage, design, plan)
    return rows_for_design(design, stage, plan)
S.run_generation_stage = run_generation_stage


def report_batch_composition(responses: pd.DataFrame, label: str) -> pd.DataFrame:
    table = pd.crosstab(responses["condition_id"], responses["batch_seed"])
    per_condition = (table > 0).sum(axis=1).rename("distinct_batches")
    single = per_condition[per_condition == 1]
    if not single.empty:
        print(f"WARNING [{label}]: single-batch conditions: {list(single.index)[:8]}")
    return per_condition.to_frame()
S.report_batch_composition = report_batch_composition


def batch_profile_summary(stage: str) -> pd.DataFrame:
    records = [r for r in S.load_jsonl(S.RUN_ROOT / f"{stage}_batch_profile.jsonl")
               if r.get("run_attempt_id") == S.RUN_ATTEMPT_ID]
    if not records:
        return pd.DataFrame([{"stage": stage, "batches_this_attempt": 0}])
    df = pd.DataFrame(records)
    gen = float(df.get("generate_seconds", pd.Series([np.nan])).sum())
    out = {"stage": stage, "run_attempt_id": S.RUN_ATTEMPT_ID,
           "batches_this_attempt": len(df), "rows": int(df["batch_size"].sum()),
           "wall_seconds": float(df["wall_seconds"].sum()),
           "generate_seconds": gen,
           "input_tokens": int(df.get("input_tokens", pd.Series([0])).sum()),
           "output_tokens": int(df.get("output_tokens", pd.Series([0])).sum()),
           "splits": int(df["split_depth"].gt(0).sum())}
    out["output_tokens_per_second"] = out["output_tokens"] / gen if gen else np.nan
    return pd.DataFrame([out])
S.batch_profile_summary = batch_profile_summary


def score_responses(responses: pd.DataFrame) -> pd.DataFrame:
    """Verify every constraint present in each response."""
    rows = []
    _TERMINATION_BY_ROW = {t["row_id"]: t for t in S.TERMINATION_RECORDS}
    with S.phase("verify"):
        for r in responses.to_dict("records"):
            ids = r["ordered_constraint_ids"]
            if isinstance(ids, str):
                ids = json.loads(ids)
            term = _TERMINATION_BY_ROW.get(r.get("row_id"), {})
            for cid in ids:
                if r.get("generation_ok", False):
                    res = S.verify(r.get("response_text", ""), cid)
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
                    "generative_scope": S.CONSTRAINTS[cid].generative_scope,
                    "status": res.status, "binary_pass": res.binary_pass,
                    "fail": 1 - res.binary_pass,
                    "continuous_score": res.continuous_score,
                    "detail_json": json.dumps(res.detail, ensure_ascii=False),
                    "generation_ok": bool(r.get("generation_ok", False)),
                    "plan_deviation": bool(r.get("plan_deviation", False)),
                    "is_synthetic": bool(r.get("is_synthetic", False)),
                    "model_profile": S.CFG.model_profile,
                    "response_words": len(word_tokens(r.get("response_text", ""))),
                    **{k: term.get(k) for k in
                       ("generated_token_count", "ended_with_eos",
                        "hit_max_new_tokens", "output_truncated", "stop_reason")},
                })
    return pd.DataFrame(rows)
S.score_responses = score_responses


def termination_frame() -> pd.DataFrame:
    return indexed_frame(
        list({t["row_id"]: t for t in S.TERMINATION_RECORDS}.values()), "row_id",
        ["row_id", "generated_token_count", "ended_with_eos",
         "hit_max_new_tokens", "output_truncated", "stop_reason"])
S.termination_frame = termination_frame


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


print(f"synthetic corpus: {len(S.SYNTHETIC_CORPUS)} responses "
      f"({len(SYN_EASY_IDX)} easy, {len(SYN_HARD_IDX)} hard)")
print(f"designed focal excess {SYN_FOCAL_EXCESS:+.2f}, order effect "
      f"{SYN_ORDER['added_first'] - SYN_ORDER['target_first']:+.2f} on the beta scale")
