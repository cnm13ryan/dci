TARGET_FIRST, ADDED_FIRST = CFG.orders


def compose_prompt(topic: str, ordered_ids: list[str], paraphrase_id: int) -> str:
    lines = "\n".join(
        f"{i}. {INSTRUCTIONS[cid][paraphrase_id]}"
        for i, cid in enumerate(ordered_ids, start=1))
    return f"{topic}\n\nSatisfy every constraint below simultaneously:\n{lines}"


def design_row(stage: str, task: dict[str, str], condition_id: str,
               ordered_ids: list[str], paraphrase_id: int, seed: int,
               added: str = "", order: str = "", measured: str = "") -> dict[str, Any]:
    """One design cell. row_id hashes stage, task, condition, wording and seed.

    It deliberately does NOT hash the model or decoding settings: those live in
    the execution fingerprint, which the cache and the restore path check
    separately, so a profile change invalidates the cache without silently
    renaming every row.
    """
    key = f"{stage}|{task['task_id']}|{condition_id}|{paraphrase_id}|{seed}"
    return {
        "row_id": hashlib.sha256(key.encode()).hexdigest()[:20],
        "stage": stage, "task_id": task["task_id"], "split": task["split"],
        "topic": task["topic"], "condition_id": condition_id,
        "added_constraint": added, "measured_constraint": measured, "order": order,
        "ordered_constraint_ids": ordered_ids, "paraphrase_id": paraphrase_id,
        "repetition_seed": seed,
        "user_prompt": compose_prompt(task["topic"], ordered_ids, paraphrase_id),
    }


def iso_condition(cid: str) -> str:
    return f"ISO|{cid}"


def pair_condition(u: str, q: str, first: str) -> str:
    assert first in (u, q)
    return f"PAIR|{u}|{q}|first={first}"


def _finalise(rows: list[dict[str, Any]], balanced: bool = False) -> pd.DataFrame:
    design = pd.DataFrame(rows)
    assert design["row_id"].is_unique, "design rows must be uniquely identified"
    if balanced:
        counts = design.groupby("condition_id").size()
        assert counts.nunique() == 1, (
            f"design must be balanced across conditions; sizes {sorted(set(counts))}")
    return design


# ------------------------------------------------------- U screening (Gate 1)
def build_screening_design() -> pd.DataFrame:
    """Isolated and neutral-paired runs for every authored U candidate."""
    partner = CFG.u_screen_partner_id
    rows = []
    for task in SCREENING_TASKS:
        for seed in CFG.screening_seeds:
            rows.append(design_row("screening", task, iso_condition(partner),
                                   [partner], CFG.prescreen_paraphrase, seed,
                                   added=partner, order="isolated", measured=partner))
            for u in U_CANDIDATE_IDS:
                rows.append(design_row("screening", task, iso_condition(u), [u],
                                       CFG.prescreen_paraphrase, seed, added=u,
                                       order="isolated", measured=u))
                rows.append(design_row(
                    "screening", task, pair_condition(u, partner, u), [u, partner],
                    CFG.prescreen_paraphrase, seed, added=partner,
                    order=TARGET_FIRST, measured=u))
    return _finalise(rows)


# --------------------------------------------------- cheap canonical prescreen
def build_prescreen_design() -> pd.DataFrame:
    """Loose isolated-difficulty screen at one wording, to narrow the pool."""
    measured = [CFG.focal_id, *CANDIDATE_IDS]
    rows = []
    for task in PRESCREEN_TASKS:
        for seed in CFG.screening_seeds:
            for cid in measured:
                rows.append(design_row("prescreen", task, iso_condition(cid), [cid],
                                       CFG.prescreen_paraphrase, seed, added=cid,
                                       order="isolated", measured=cid))
    return _finalise(rows)


# --------------------------------------------------------------- calibration
def build_calibration_design(constraint_ids: Iterable[str], u_pairs: Iterable[str],
                             paraphrase_ids: Iterable[int], stage: str,
                             tasks: Optional[list[dict[str, str]]] = None
                             ) -> pd.DataFrame:
    """Isolated runs plus k=2 runs against the given unrelated targets, both orders.

    Every quantity is measured against unrelated targets, so nothing in the
    calibration signature is a post-treatment function of the confirmatory
    outcome.
    """
    constraint_ids, u_pairs = list(constraint_ids), list(u_pairs)
    paraphrase_ids = list(paraphrase_ids)
    tasks = CALIBRATION_TASKS if tasks is None else tasks
    rows = []
    for task in tasks:
        for p in paraphrase_ids:
            for seed in CFG.calibration_seeds:
                for cid in constraint_ids:
                    rows.append(design_row(stage, task, iso_condition(cid), [cid],
                                           p, seed, added=cid, order="isolated",
                                           measured=cid))
                for u in u_pairs:
                    rows.append(design_row(stage, task, iso_condition(u), [u], p,
                                           seed, added=u, order="isolated", measured=u))
                    for cid in constraint_ids:
                        rows.append(design_row(
                            stage, task, pair_condition(u, cid, u), [u, cid], p,
                            seed, added=cid, order=TARGET_FIRST, measured=u))
                        rows.append(design_row(
                            stage, task, pair_condition(u, cid, cid), [cid, u], p,
                            seed, added=cid, order=ADDED_FIRST, measured=u))
    return _finalise(rows)


def build_wording_validation_design(constraint_ids: Iterable[str],
                                    u_targets: Iterable[str]) -> pd.DataFrame:
    """Gate 3b. The same comparability measurement under the held-out wordings.

    It deliberately measures the calibration signature and not the A outcome:
    the held-out wordings must never contribute to the primary estimand, and
    looking at a tau-like quantity before the freeze would be exactly the
    pre-confirmatory peek the design forbids.
    """
    return build_calibration_design(constraint_ids, u_targets,
                                    list(CFG.paraphrase_holdout),
                                    "wording_validation", WORDING_TASKS)


# --------------------------------------------------------------- confirmatory
def build_confirmatory_design(references: list[str],
                              paraphrase_ids: Iterable[int]) -> pd.DataFrame:
    added_set = [CFG.focal_id, *references]
    rows = []
    for task in CONFIRMATORY_TASKS:
        for p in paraphrase_ids:
            for seed in CFG.confirmatory_seeds:
                rows.append(design_row("confirmatory", task, "A_ONLY",
                                       [CFG.target_id], p, seed, added="none",
                                       order="none", measured=CFG.target_id))
                for cid in added_set:
                    rows.append(design_row(
                        "confirmatory", task, f"{cid}|{TARGET_FIRST}",
                        [CFG.target_id, cid], p, seed, cid, TARGET_FIRST, CFG.target_id))
                    rows.append(design_row(
                        "confirmatory", task, f"{cid}|{ADDED_FIRST}",
                        [cid, CFG.target_id], p, seed, cid, ADDED_FIRST, CFG.target_id))
    return _finalise(rows, balanced=True)


# ------------------------------------------------------ U_test falsification
def build_placebo_design(references: list[str], u_test: Iterable[str],
                         paraphrase_ids: Iterable[int]) -> pd.DataFrame:
    rows = []
    for task in PLACEBO_TASKS:
        for p in paraphrase_ids:
            for seed in CFG.confirmatory_seeds:
                for u in u_test:
                    rows.append(design_row("placebo", task, f"{u}|ONLY", [u], p,
                                           seed, added="none", order="none", measured=u))
                    for cid in [CFG.focal_id, *references]:
                        rows.append(design_row(
                            "placebo", task, f"{u}|{cid}|{TARGET_FIRST}", [u, cid],
                            p, seed, cid, TARGET_FIRST, u))
                        rows.append(design_row(
                            "placebo", task, f"{u}|{cid}|{ADDED_FIRST}", [cid, u],
                            p, seed, cid, ADDED_FIRST, u))
    return _finalise(rows)


# ------------------------------------------------------------------ benchmark
BENCHMARK_PROMPTS = [
    "Write a short paragraph about clouds.",
    "Describe a wooden chair in a few sentences.",
    "Explain what a doorway is for.",
    "Write briefly about the colour blue.",
    "Describe the sound of rain on a roof.",
    "Write a short paragraph about walking.",
    "Explain what a shelf holds.",
    "Describe a paper envelope.",
]


def build_benchmark_design(n: int) -> pd.DataFrame:
    """Frozen non-scientific prompts. These never enter any scientific stage."""
    rows = []
    for i in range(n):
        text = BENCHMARK_PROMPTS[i % len(BENCHMARK_PROMPTS)]
        task = {"task_id": f"BENCH{i:03d}", "split": "benchmark", "topic": text}
        rows.append({
            "row_id": hashlib.sha256(f"benchmark|{i}".encode()).hexdigest()[:20],
            "stage": "benchmark", "task_id": task["task_id"], "split": "benchmark",
            "topic": text, "condition_id": "BENCH", "added_constraint": "none",
            "measured_constraint": "", "order": "none",
            "ordered_constraint_ids": [], "paraphrase_id": 0,
            "repetition_seed": CFG.base_seed, "user_prompt": text})
    return pd.DataFrame(rows)


# --------------------------------------------------------- generation budget
def generation_budget(n_candidates: int, paraphrases: int,
                      seconds_per_generation: float) -> pd.DataFrame:
    n_u = len(U_CANDIDATE_IDS)
    n_build = CFG.u_per_split
    n_val_targets = CFG.u_per_split + 1          # build families plus one bridge
    n_val_constraints = CFG.reference_count + 3  # panel plus near misses
    n_cal_blocks = len(CALIBRATION_TASKS) * paraphrases * len(CFG.calibration_seeds)
    n_conf_blocks = len(CONFIRMATORY_TASKS) * paraphrases * len(CFG.confirmatory_seeds)
    n_plac_blocks = len(PLACEBO_TASKS) * paraphrases * len(CFG.confirmatory_seeds)
    n_word_blocks = (len(WORDING_TASKS) * len(CFG.paraphrase_holdout)
                     * len(CFG.calibration_seeds))
    panel = CFG.reference_count + 1

    stages = [
        ("screening", len(SCREENING_TASKS) * len(CFG.screening_seeds) * (1 + 2 * n_u),
         "Gate 1"),
        ("prescreen", len(PRESCREEN_TASKS) * len(CFG.screening_seeds)
         * (1 + len(CANDIDATE_IDS)), "pool narrowing"),
        ("calibration_u_build", n_cal_blocks * ((n_candidates + 1) + n_build
                                                + 2 * n_build * (n_candidates + 1)),
         "Gate 2"),
        ("calibration_u_val", n_cal_blocks * (n_val_constraints + n_val_targets
                                              + 2 * n_val_targets * n_val_constraints),
         "Gate 3"),
        ("wording_validation", n_word_blocks * (panel + n_val_targets
                                                + 2 * n_val_targets * panel),
         "Gate 3b"),
        ("confirmatory", n_conf_blocks * (1 + 2 * panel), "primary"),
        ("placebo", n_plac_blocks * n_val_targets * (1 + 2 * panel), "Gate 4"),
    ]
    table = pd.DataFrame(stages, columns=["stage", "generations", "buys"])
    table["hours"] = table["generations"] * seconds_per_generation / 3600
    table["cumulative_hours"] = table["hours"].cumsum()
    pre = table[~table["stage"].isin(["confirmatory", "placebo"])]
    table.attrs["pre_freeze_hours"] = float(pre["hours"].sum())
    return table


SECONDS_PER_GENERATION = CFG.benchmark_seconds_per_generation_default
BUDGET = generation_budget(len(CANDIDATE_IDS), min(CFG.paraphrase_schedule),
                           SECONDS_PER_GENERATION)
display(BUDGET.round(2))
BUDGET.to_csv(DESIGN_DIR / "generation_budget.csv", index=False)
_post = float(BUDGET[BUDGET["stage"].isin(["confirmatory", "placebo"])]["hours"].sum())
print(f"""
Budget at {SECONDS_PER_GENERATION} s per generation, {min(CFG.paraphrase_schedule)} wordings, before caching.
This rate is a PLACEHOLDER until the benchmark cell measures the real one for
profile '{CFG.model_profile}'.

  Everything through Gate 3b : {BUDGET.attrs['pre_freeze_hours']:.1f} h, and any of it can stop the study
  Confirmatory and Gate 4    : {_post:.1f} h, authorised only after Gate 3b passes
""")
