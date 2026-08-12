"""Scientific seeds, derived from scientific identity and nothing else.

The historical defect this module exists to prevent: the first reasoning grid
used ONE shared seed for all 160 requests, so the two nominal replicates of a
cell were byte-identical and "2 replicates" was one draw counted twice
(390/400 identical — see `REASONING_DATA_PROVENANCE.md`). The fix at the time
was `20260810 + offset + 7919 * i`, where `i` is the row's **index in the design
file**. That removes the duplication but makes the seed a function of position:
re-order the design, shard it across two GPUs, or let a backend re-batch it, and
the same scientific cell draws a different sample.

Here the seed is a pure function of the cell's stable scientific identity:

    (MASTER_SEED, task_id, replicate, arm, background, order, paraphrase, phase)

Nothing about position, generation order, device, shard or batch enters. Two
consequences follow, and both are wanted:

* The design can be sharded across the two GPUs in any partition, merged in any
  order, or re-run row by row, and every cell keeps its own draw.
* The seed is NOT a function of the model, so the `scientific_seed` column is
  comparable across checkpoints. It does not make two checkpoints produce the
  same text — different weights and tokenizers see the same integer differently —
  and no such equivalence is claimed.

`phase` separates the reasoning pass from the answer pass of the two-phase
splice, so the answer continuation is not drawing on the reasoning pass's stream.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable

#: Seeds are fed to torch/numpy generators; stay inside a comfortable 63-bit
#: range rather than relying on every backend accepting a full 64-bit unsigned.
_SEED_MODULUS = 2 ** 31 - 1

REASONING_PHASE = "reasoning"
ANSWER_PHASE = "answer"

#: The fields that constitute a row's scientific identity. Anything not on this
#: list is an execution detail and must not reach the seed.
IDENTITY_FIELDS = ("task_id", "replicate", "arm", "variant", "order",
                   "paraphrase_id")


def scientific_seed(master_seed: int, *, task_id: str, replicate: int, arm: str,
                    background: str, order: str, paraphrase_id: int,
                    phase: str) -> int:
    """A deterministic, position-independent seed for one generation."""
    if phase not in (REASONING_PHASE, ANSWER_PHASE):
        raise ValueError(f"unknown generation phase {phase!r}")
    material = "|".join(str(part) for part in (
        master_seed, task_id, replicate, arm, background, order,
        paraphrase_id, phase))
    digest = hashlib.sha256(material.encode()).digest()
    return int.from_bytes(digest[:8], "big") % _SEED_MODULUS


def seed_for_row(row: Any, master_seed: int, phase: str) -> int:
    """`scientific_seed` for a design row (dataclass or mapping)."""
    def get(name: str) -> Any:
        return row[name] if isinstance(row, dict) else getattr(row, name)

    return scientific_seed(
        master_seed, task_id=get("task_id"), replicate=int(get("replicate")),
        arm=get("arm"), background=get("variant"), order=get("order"),
        paraphrase_id=int(get("paraphrase_id")), phase=phase)


# ------------------------------------------------------------------- guards
def assert_seed_regime(rows: Iterable[Any], master_seed: int) -> dict[str, Any]:
    """Every scientific cell has its own seed, and every row its own id.

    Returns the audit rather than only raising, so the run manifest can record
    what was checked instead of asserting that something was checked.
    """
    rows = list(rows)
    seeds: dict[int, list[str]] = {}
    row_ids: dict[str, int] = {}
    cells: set[tuple] = set()

    for row in rows:
        def get(name: str) -> Any:
            return row[name] if isinstance(row, dict) else getattr(row, name)

        seed = seed_for_row(row, master_seed, REASONING_PHASE)
        seeds.setdefault(seed, []).append(get("row_id"))
        row_ids[get("row_id")] = row_ids.get(get("row_id"), 0) + 1
        cells.add(tuple(str(get(f)) for f in IDENTITY_FIELDS))

    collisions = {seed: ids for seed, ids in seeds.items() if len(ids) > 1}
    duplicate_ids = {rid: n for rid, n in row_ids.items() if n > 1}

    audit = {
        "rows": len(rows),
        "unique_scientific_seeds": len(seeds),
        "unique_row_ids": len(row_ids),
        "unique_scientific_cells": len(cells),
        "seed_collisions": {str(k): v for k, v in collisions.items()},
        "duplicate_row_ids": duplicate_ids,
        "master_seed": master_seed,
    }
    problems = []
    if collisions:
        problems.append(f"{len(collisions)} seed collision(s): {collisions}")
    if duplicate_ids:
        problems.append(f"duplicate row ids: {duplicate_ids}")
    if len(cells) != len(rows):
        problems.append(
            f"{len(rows)} rows occupy only {len(cells)} distinct scientific "
            "cells; the design has a missing or duplicated cell")
    if problems:
        raise AssertionError("seed regime is invalid: " + "; ".join(problems))
    return audit


def replicate_duplication(records: Iterable[dict[str, Any]],
                          answer_field: str = "final_answer",
                          ) -> dict[str, Any]:
    """Identical final-answer pairs over nominal replicate pairs.

    Stochastic decoding CAN coincide, especially on short answers, so a nonzero
    count is not by itself a defect. A majority is the signature of a shared
    seed. The alarm threshold is the repository's existing one (25%).

    Pairs in which either replicate produced NO final answer are excluded. Two
    empty strings compare equal without either being a sample, so counting them
    lets a checkpoint that often reaches its token ceiling manufacture an
    apparent seed collapse out of nothing — and, worse, pads the denominator so
    a real collapse among the answered rows is diluted out of sight.
    `pairs_without_answer` records how many were set aside, so the exclusion is
    visible rather than silent.
    """
    groups: dict[tuple, list[str]] = {}
    for record in records:
        key = (record.get("model_id"), record.get("reasoning_mode"),
               record.get("task_id"), record.get("arm"),
               record.get("background"))
        groups.setdefault(key, []).append(record.get(answer_field) or "")

    complete = [answers for answers in groups.values() if len(answers) == 2]
    answered = [answers for answers in complete
                if answers[0].strip() and answers[1].strip()]
    identical = sum(1 for answers in answered if answers[0] == answers[1])
    rate = identical / len(answered) if answered else float("nan")
    return {"replicate_pairs": len(answered),
            "nominal_replicate_pairs": len(complete),
            "pairs_without_answer": len(complete) - len(answered),
            "identical_pairs": identical,
            "identical_rate": rate, "alarm_threshold": 0.25,
            "implausible": bool(answered) and rate >= 0.25}
