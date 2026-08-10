"""Stage 182 — migrated from notebook cell 182.py (design_builders).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/182.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.constraints.satisfiability import assert_design_is_satisfiable, pair_verdict  # noqa: F401


S.TARGET_FIRST, S.ADDED_FIRST = S.CFG.orders


def compose_prompt(topic: str, ordered_ids: list[str], paraphrase_id: int) -> str:
    lines = "\n".join(
        f"{i}. {S.INSTRUCTIONS[cid][paraphrase_id]}"
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
S.iso_condition = iso_condition


def pair_condition(u: str, q: str, first: str) -> str:
    assert first in (u, q)
    return f"PAIR|{u}|{q}|first={first}"
S.pair_condition = pair_condition


def _finalise(rows: list[dict[str, Any]], balanced: bool = False) -> pd.DataFrame:
    design = pd.DataFrame(rows)
    assert design["row_id"].is_unique, "design rows must be uniquely identified"
    if balanced:
        counts = design.groupby("condition_id").size()
        assert counts.nunique() == 1, (
            f"design must be balanced across conditions; sizes {sorted(set(counts))}")
    # v15.1: the single choke point every builder passes through, so no design --
    # screening, prescreen, calibration, wording, confirmatory or placebo -- can
    # contain a pair that is known not to be jointly satisfiable. Measured failure
    # on such a row records impossibility, not compositional burden.
    assert_design_is_satisfiable(design, S.CONSTRAINTS,
                                 label=str(design["stage"].iloc[0]) if len(design)
                                 else "design")
    return design


# ------------------------------------------------------- U screening (Gate 1)
def build_screening_design() -> pd.DataFrame:
    """Isolated and neutral-paired runs for every authored U candidate."""
    partner = S.CFG.u_screen_partner_id
    rows = []
    for task in S.SCREENING_TASKS:
        for seed in S.CFG.screening_seeds:
            rows.append(design_row("screening", task, S.iso_condition(partner),
                                   [partner], S.CFG.prescreen_paraphrase, seed,
                                   added=partner, order="isolated", measured=partner))
            for u in S.U_CANDIDATE_IDS:
                rows.append(design_row("screening", task, S.iso_condition(u), [u],
                                       S.CFG.prescreen_paraphrase, seed, added=u,
                                       order="isolated", measured=u))
                rows.append(design_row(
                    "screening", task, S.pair_condition(u, partner, u), [u, partner],
                    S.CFG.prescreen_paraphrase, seed, added=partner,
                    order=S.TARGET_FIRST, measured=u))
    return _finalise(rows)
S.build_screening_design = build_screening_design


# --------------------------------------------------- cheap canonical prescreen
def build_prescreen_design() -> pd.DataFrame:
    """Loose isolated-difficulty screen at one wording, to narrow the pool."""
    measured = [S.CFG.focal_id, *S.CANDIDATE_IDS]
    rows = []
    for task in S.PRESCREEN_TASKS:
        for seed in S.CFG.screening_seeds:
            for cid in measured:
                rows.append(design_row("prescreen", task, S.iso_condition(cid), [cid],
                                       S.CFG.prescreen_paraphrase, seed, added=cid,
                                       order="isolated", measured=cid))
    return _finalise(rows)
S.build_prescreen_design = build_prescreen_design


# --------------------------------------------------------------- calibration
def build_calibration_design(constraint_ids: Iterable[str], u_pairs: Iterable[str],
                             paraphrase_ids: Iterable[int], stage: str,
                             tasks: Optional[list[dict[str, str]]] = None
                             ) -> pd.DataFrame:
    """Isolated runs plus k=2 runs against the given unrelated targets, both orders.

    Every quantity is measured against unrelated targets, so nothing in the
    calibration signature is a post-treatment function of the confirmatory
    outcome.

    v15.1 refuses candidate-U pairings that are not jointly satisfiable. A
    contradiction here does not merely waste a generation: g and r are LEARNED
    from these pairings, so forced failure on an impossible pair enters the
    behavioural signature, changes which candidates qualify as references, and
    thereby changes the comparison class that defines tau.
    """
    constraint_ids, u_pairs = list(constraint_ids), list(u_pairs)
    paraphrase_ids = list(paraphrase_ids)
    tasks = S.CALIBRATION_TASKS if tasks is None else tasks

    # Candidate-U pairings that are not jointly satisfiable are EXCLUDED, not
    # generated and then explained away. The dev_fast validation design contained
    # 288 rows pairing U_FMT_SEMI2 ("exactly two semicolons in the answer") with
    # S_SEMICOLON ("a semicolon in every sentence"), which is satisfiable only
    # when the answer has exactly two sentences. Forced failure on such a row
    # would enter g and r and thereby the reference definition.
    #
    # Excluding a pairing REDUCES support for that component rather than
    # distorting it, and the reduction is visible: Gate 2's common-support report
    # names any component that loses its pool, and the exclusion is logged as a
    # departure so it cannot pass unnoticed.
    _EXCLUDED_CALIBRATION_PAIRS = set()
    for u in u_pairs:
        for cid in constraint_ids:
            kind, why = pair_verdict(S.CONSTRAINTS[u], S.CONSTRAINTS[cid]) \
                if u in S.CONSTRAINTS and cid in S.CONSTRAINTS else ("ok", "")
            if kind != "ok":
                _EXCLUDED_CALIBRATION_PAIRS.add((u, cid))
    if _EXCLUDED_CALIBRATION_PAIRS:
        S.CALIBRATION_PAIRS_EXCLUDED = sorted(
            getattr(S, "CALIBRATION_PAIRS_EXCLUDED", []) +
            [f"{stage}:{u}+{cid}" for u, cid in _EXCLUDED_CALIBRATION_PAIRS])
        S.log_departure(
            "calibration_design",
            f"{stage} crosses every candidate with every unrelated target",
            f"{len(_EXCLUDED_CALIBRATION_PAIRS)} candidate-U pairing(s) excluded "
            "as not jointly satisfiable: "
            + ", ".join(f"{u}+{cid}" for u, cid in sorted(_EXCLUDED_CALIBRATION_PAIRS)),
            "measured failure on a logically impossible pair records "
            "impossibility, not compositional burden; the affected g/r components "
            "lose support rather than carrying a distorted value")

    rows = []
    for task in tasks:
        for p in paraphrase_ids:
            for seed in S.CFG.calibration_seeds:
                for cid in constraint_ids:
                    rows.append(design_row(stage, task, S.iso_condition(cid), [cid],
                                           p, seed, added=cid, order="isolated",
                                           measured=cid))
                for u in u_pairs:
                    rows.append(design_row(stage, task, S.iso_condition(u), [u], p,
                                           seed, added=u, order="isolated", measured=u))
                    for cid in constraint_ids:
                        if (u, cid) in _EXCLUDED_CALIBRATION_PAIRS:
                            continue
                        rows.append(design_row(
                            stage, task, S.pair_condition(u, cid, u), [u, cid], p,
                            seed, added=cid, order=S.TARGET_FIRST, measured=u))
                        rows.append(design_row(
                            stage, task, S.pair_condition(u, cid, cid), [cid, u], p,
                            seed, added=cid, order=S.ADDED_FIRST, measured=u))
    return _finalise(rows)
S.build_calibration_design = build_calibration_design


def build_wording_validation_design(constraint_ids: Iterable[str],
                                    u_targets: Iterable[str]) -> pd.DataFrame:
    """Gate 3b. The same comparability measurement under the held-out wordings.

    It deliberately measures the calibration signature and not the A outcome:
    the held-out wordings must never contribute to the primary estimand, and
    looking at a tau-like quantity before the freeze would be exactly the
    pre-confirmatory peek the design forbids.
    """
    return S.build_calibration_design(constraint_ids, u_targets,
                                    list(S.CFG.paraphrase_holdout),
                                    "wording_validation", S.WORDING_TASKS)
S.build_wording_validation_design = build_wording_validation_design


# --------------------------------------------------------------- confirmatory
def build_confirmatory_design(references: list[str],
                              paraphrase_ids: Iterable[int]) -> pd.DataFrame:
    added_set = [S.CFG.focal_id, *references]
    rows = []
    for task in S.CONFIRMATORY_TASKS:
        for p in paraphrase_ids:
            for seed in S.CFG.confirmatory_seeds:
                rows.append(design_row("confirmatory", task, "A_ONLY",
                                       [S.CFG.target_id], p, seed, added="none",
                                       order="none", measured=S.CFG.target_id))
                for cid in added_set:
                    rows.append(design_row(
                        "confirmatory", task, f"{cid}|{S.TARGET_FIRST}",
                        [S.CFG.target_id, cid], p, seed, cid, S.TARGET_FIRST, S.CFG.target_id))
                    rows.append(design_row(
                        "confirmatory", task, f"{cid}|{S.ADDED_FIRST}",
                        [cid, S.CFG.target_id], p, seed, cid, S.ADDED_FIRST, S.CFG.target_id))
    return _finalise(rows, balanced=True)
S.build_confirmatory_design = build_confirmatory_design


# ------------------------------------------------------ U_test falsification
def build_placebo_design(references: list[str], u_test: Iterable[str],
                         paraphrase_ids: Iterable[int]) -> pd.DataFrame:
    rows = []
    for task in S.PLACEBO_TASKS:
        for p in paraphrase_ids:
            for seed in S.CFG.confirmatory_seeds:
                for u in u_test:
                    rows.append(design_row("placebo", task, f"{u}|ONLY", [u], p,
                                           seed, added="none", order="none", measured=u))
                    for cid in [S.CFG.focal_id, *references]:
                        rows.append(design_row(
                            "placebo", task, f"{u}|{cid}|{S.TARGET_FIRST}", [u, cid],
                            p, seed, cid, S.TARGET_FIRST, u))
                        rows.append(design_row(
                            "placebo", task, f"{u}|{cid}|{S.ADDED_FIRST}", [cid, u],
                            p, seed, cid, S.ADDED_FIRST, u))
    return _finalise(rows)
S.build_placebo_design = build_placebo_design


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
            "repetition_seed": S.CFG.base_seed, "user_prompt": text})
    return pd.DataFrame(rows)
S.build_benchmark_design = build_benchmark_design


# --------------------------------------------------------- generation budget
def generation_budget(n_candidates: int, paraphrases: int,
                      seconds_per_generation: float) -> pd.DataFrame:
    n_u = len(S.U_CANDIDATE_IDS)
    n_build = S.CFG.u_per_split
    n_val_targets = S.CFG.u_per_split + 1          # build families plus one bridge
    n_val_constraints = S.CFG.reference_count + 3  # panel plus near misses
    n_cal_blocks = len(S.CALIBRATION_TASKS) * paraphrases * len(S.CFG.calibration_seeds)
    n_conf_blocks = len(S.CONFIRMATORY_TASKS) * paraphrases * len(S.CFG.confirmatory_seeds)
    n_plac_blocks = len(S.PLACEBO_TASKS) * paraphrases * len(S.CFG.confirmatory_seeds)
    n_word_blocks = (len(S.WORDING_TASKS) * len(S.CFG.paraphrase_holdout)
                     * len(S.CFG.calibration_seeds))
    panel = S.CFG.reference_count + 1

    stages = [
        ("screening", len(S.SCREENING_TASKS) * len(S.CFG.screening_seeds) * (1 + 2 * n_u),
         "Gate 1"),
        ("prescreen", len(S.PRESCREEN_TASKS) * len(S.CFG.screening_seeds)
         * (1 + len(S.CANDIDATE_IDS)), "pool narrowing"),
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
S.generation_budget = generation_budget


S.SECONDS_PER_GENERATION = S.CFG.benchmark_seconds_per_generation_default
BUDGET = S.generation_budget(len(S.CANDIDATE_IDS), min(S.CFG.paraphrase_schedule),
                           S.SECONDS_PER_GENERATION)
display(BUDGET.round(2))
BUDGET.to_csv(S.DESIGN_DIR / "generation_budget.csv", index=False)
_post = float(BUDGET[BUDGET["stage"].isin(["confirmatory", "placebo"])]["hours"].sum())
print(f"""
Budget at {S.SECONDS_PER_GENERATION} s per generation, {min(S.CFG.paraphrase_schedule)} wordings, before caching.
This rate is a PLACEHOLDER until the benchmark cell measures the real one for
profile '{S.CFG.model_profile}'.

  Everything through Gate 3b : {BUDGET.attrs['pre_freeze_hours']:.1f} h, and any of it can stop the study
  Confirmatory and Gate 4    : {_post:.1f} h, authorised only after Gate 3b passes
""")
