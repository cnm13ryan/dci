"""The ONE scientific contract every checkpoint must satisfy.

This module is the single place that states what the cross-model replication
holds fixed. It is deliberately tiny and deliberately declarative: the whole
point of the cross-model study is that the *science* does not vary while the
*execution* does, and a contract scattered across five runner scripts is not a
contract.

Nothing here is re-typed from prose. The constraint ids, wordings, task bank,
prompt assembly and verifiers all come from the v15/v19 registry through
`dci_exploratory.harvest`; this module only names WHICH of them the frozen slice
uses, and those names were read off the canonical run's own `config.json`:

    runs/stageS18_reasoning_design_20260811T144250Z/config.json
      --target A --focal B --arms C_L3
      --background X_SEMICOLON_FREE,X_PAREN_FREE
      --load 3 --permute QAC --tasks 20 --replicates 2

If any value below stops matching that config, the cross-model run has stopped
replicating the study it claims to replicate. `assert_matches_canonical_run`
checks exactly that against a run directory.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --------------------------------------------------------------- the slice
#: The instruction whose compliance is scored. F_A = 1 means A failed.
TARGET = "A"                    # "Write exactly 4 sentences."

#: The focal instruction B, whose interference onto A is the estimand.
FOCAL = "B"                     # "Make each sentence strictly longer ..."

#: The matched reference R. Focal and reference rows differ in this slot ONLY.
REFERENCE = "C_L3"              # "Begin every sentence with a word ... S."

#: The background-slot occupants. `CONTROL_BACKGROUND` is the bracket/control
#: condition; `SEMICOLON_BACKGROUND` is the amplifying one. They differ in one
#: phrase and in nothing else.
CONTROL_BACKGROUND = "X_PAREN_FREE"
SEMICOLON_BACKGROUND = "X_SEMICOLON_FREE"

ARMS = (FOCAL, REFERENCE)
BACKGROUNDS = (SEMICOLON_BACKGROUND, CONTROL_BACKGROUND)

#: Frozen canonical instruction order: focal slot, target, background slot.
ORDER = "QAC"

#: Three instructions per prompt.
LOAD = 3

#: The task bank slice: the first 20 tasks of the `pilot` split, in bank order.
TASK_SPLIT = "pilot"
TASK_OFFSET = 0
N_TASKS = 20

#: Scientific replicates per cell.
REPLICATES = 2

#: Wording index. The study has never varied this in the reasoning line of work.
PARAPHRASE_ID = 0

#: 2 arms x 2 backgrounds x 20 tasks x 2 replicates.
EXPECTED_ROWS = len(ARMS) * len(BACKGROUNDS) * N_TASKS * REPLICATES   # 160

#: Answer allowance, identical in every condition and every model. This is the
#: contract's own number, not a per-model tuning knob: if one checkpoint were
#: given more room to answer than another, a length-sensitive verifier
#: ("exactly 4 sentences") would be measuring the allowance.
ANSWER_TOKENS = 512

#: Decoding, identical across checkpoints. Read off the canonical run.
TEMPERATURE = 0.7
TOP_P = 0.9
#: The canonical vLLM run left top_k unset, i.e. disabled. Transformers defaults
#: top_k to 50, which would silently narrow the sampling support relative to the
#: canonical condition, so every adapter must disable it explicitly.
TOP_K = 0

#: Master seed for the scientific seed regime. See `crossmodel.seeds`.
MASTER_SEED = 20260812

#: Task-cluster bootstrap draws. The repository uses 4000
#: (`dci_exploratory.plotstyle.BOOTSTRAP_DRAWS`), NOT 10,000; this constant is
#: imported from there at analysis time rather than restated, and is recorded
#: here only so the contract document can report what was used.
BOOTSTRAP_DRAWS_SOURCE = "dci_exploratory.plotstyle.BOOTSTRAP_DRAWS"

#: The canonical run this slice replicates, for provenance.
CANONICAL_RUN = "stageS18_reasoning_design_20260811T144250Z"
CANONICAL_MODEL = "Qwen/Qwen3-4B"
CANONICAL_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
CANONICAL_BACKEND = "vllm 0.15.1+rocm720, tensor_parallel_size=2"


# ------------------------------------------------------------ reasoning modes
class ReasoningMode:
    """Semantic labels. A backend default is never a reasoning condition.

    These are *experimental conditions*, not implementation details. A model
    supports a subset of them, and a mode it does not natively support is a
    missing cell, never something to emulate.
    """

    NO_THINKING = "NO_THINKING"
    LIMITED_REASONING = "LIMITED_REASONING"
    NATURAL_REASONING = "NATURAL_REASONING"
    #: Thinking on, no assigned budget, but a ceiling low enough that some
    #: requests reach it. Distinct from NATURAL_REASONING, where the ceiling is
    #: set far above observed reasoning length and never binds, and from
    #: LIMITED_REASONING, where the number IS the treatment. Here the number is
    #: an execution limit the analysis must report, never a dose.
    THINKING_ENABLED_BOUNDED = "THINKING_ENABLED_BOUNDED"

    ALL = (NO_THINKING, LIMITED_REASONING, NATURAL_REASONING,
           THINKING_ENABLED_BOUNDED)
    #: Modes in which the model reasons and closes its own reasoning.
    THINKING = (NATURAL_REASONING, THINKING_ENABLED_BOUNDED)


@dataclass(frozen=True)
class Slice:
    """The resolved slice: contract constants plus the harvested task list."""

    tasks: tuple[dict[str, str], ...]
    target: str = TARGET
    focal: str = FOCAL
    reference: str = REFERENCE
    backgrounds: tuple[str, ...] = BACKGROUNDS
    order: str = ORDER
    load: int = LOAD
    replicates: int = REPLICATES
    paraphrase_id: int = PARAPHRASE_ID

    @property
    def arms(self) -> tuple[str, ...]:
        return (self.focal, self.reference)

    @property
    def expected_rows(self) -> int:
        return (len(self.arms) * len(self.backgrounds)
                * len(self.tasks) * self.replicates)


def resolve_tasks(state: Any) -> tuple[dict[str, str], ...]:
    """The frozen 20 tasks, taken from the registry rather than transcribed."""
    bank = state.TASKS
    pilot = bank[bank["split"] == TASK_SPLIT]
    chosen = pilot.iloc[TASK_OFFSET:TASK_OFFSET + N_TASKS]
    if len(chosen) != N_TASKS:
        raise ValueError(
            f"the {TASK_SPLIT} split yielded {len(chosen)} tasks at offset "
            f"{TASK_OFFSET}, not {N_TASKS}; the task bank has changed and the "
            "cross-model slice is no longer the canonical one")
    return tuple({"task_id": row.task_id, "topic": row.topic}
                 for row in chosen.itertuples())


def resolve_slice(state: Any) -> Slice:
    return Slice(tasks=resolve_tasks(state))


def instruction_wordings(state: Any) -> dict[str, str]:
    """The exact sentence each constraint id contributes at PARAPHRASE_ID."""
    return {cid: state.INSTRUCTIONS[cid][PARAPHRASE_ID]
            for cid in (TARGET, FOCAL, REFERENCE, *BACKGROUNDS)}


def as_dict(state: Any | None = None) -> dict[str, Any]:
    """The whole contract, machine-readable, for the run manifest."""
    out: dict[str, Any] = {
        "target": TARGET, "focal": FOCAL, "reference": REFERENCE,
        "control_background": CONTROL_BACKGROUND,
        "semicolon_background": SEMICOLON_BACKGROUND,
        "order": ORDER, "load": LOAD,
        "task_split": TASK_SPLIT, "task_offset": TASK_OFFSET,
        "n_tasks": N_TASKS, "replicates": REPLICATES,
        "paraphrase_id": PARAPHRASE_ID, "expected_rows": EXPECTED_ROWS,
        "answer_tokens": ANSWER_TOKENS,
        "temperature": TEMPERATURE, "top_p": TOP_P, "top_k": TOP_K,
        "master_seed": MASTER_SEED,
        "replicates_canonical_run": CANONICAL_RUN,
        "canonical_model": CANONICAL_MODEL,
        "canonical_revision": CANONICAL_REVISION,
        "canonical_backend": CANONICAL_BACKEND,
    }
    if state is not None:
        out["instruction_wordings"] = instruction_wordings(state)
        out["system_message"] = state.SYSTEM_MESSAGE
        out["task_ids"] = [t["task_id"] for t in resolve_tasks(state)]
    return out


def assert_matches_canonical_run(run_dir: str | Path) -> None:
    """Refuse to claim replication if the canonical config says otherwise.

    Reads the canonical run's own argv and checks the six values that define the
    slice. This is a guard against the contract drifting away from the thing it
    was copied from — the failure mode where a later edit "tidies" a constant and
    the cross-model study silently stops being comparable.
    """
    config = json.loads((Path(run_dir) / "config.json").read_text())
    argv = config["argv"]

    def flag(name: str) -> str:
        return argv[argv.index(name) + 1]

    problems = []
    if flag("--target") != TARGET:
        problems.append(f"target {flag('--target')} != {TARGET}")
    if flag("--focal") != FOCAL:
        problems.append(f"focal {flag('--focal')} != {FOCAL}")
    if flag("--arms") != REFERENCE:
        problems.append(f"reference {flag('--arms')} != {REFERENCE}")
    if set(flag("--background").split(",")) != set(BACKGROUNDS):
        problems.append(f"backgrounds {flag('--background')} != {BACKGROUNDS}")
    if flag("--permute") != ORDER:
        problems.append(f"order {flag('--permute')} != {ORDER}")
    if int(flag("--load")) != LOAD:
        problems.append(f"load {flag('--load')} != {LOAD}")
    if int(flag("--tasks")) != N_TASKS:
        problems.append(f"tasks {flag('--tasks')} != {N_TASKS}")
    if int(flag("--replicates")) != REPLICATES:
        problems.append(f"replicates {flag('--replicates')} != {REPLICATES}")
    if config["task_ids"] != list(config["task_ids"]):   # shape check only
        problems.append("task_ids malformed")
    if problems:
        raise AssertionError(
            "the cross-model contract no longer matches the canonical run "
            f"{run_dir}: " + "; ".join(problems))
