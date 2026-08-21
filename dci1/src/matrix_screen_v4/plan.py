"""The registered §8.1 matrix, the §8.4 allocation, and the screen seed stream.

Nothing about the design is invented here. The cell set is §8.1, the wording
allocation is §8.4 verbatim, the prompt template is §8.5, and the draw count is
the registered M. What is screen-specific is the topic set (48 blocks, not
384), the stem factor, and the difficulty-spanning arm, which is decision V5's
alternative made measurable rather than assumed away.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Mapping, Sequence

from dci1v4.design.prompts import prompt_hash
from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.hashing import domain_int

from cal_screen_v4.plan import cell_wording
from fs_screen_v4.plan import (STEM_LEVELS, STEM_SENTENCE, render,
                               stem_satisfied)

#: Drawn fresh. Distinct from every v3 root (202608170-175), every v4 root
#: (202608190-195), and the three screen roots (202608200, 210, 220).
SCREEN_ROOT_SEED = 202608230
DOMAIN_SCREEN_GENERATION = "matrix:gen:v1"
STAGE = "matrix-screen"
N_WORDINGS = 4

#: §8.2. All M enter the cell mean; no draw is selected, discarded or replaced.
DRAWS = C.M_DRAWS

#: The V5 spanning arm. Two extra severities per admitted family, targeted at
#: these signed offsets from the matched companion's solo compliance, so that
#: D(B<-companion) can be read against companion difficulty instead of being
#: estimated only where difficulty is held constant.
SPANNING_OFFSETS: tuple[float, ...] = (-0.25, +0.20)


def screen_seed(model_id: str, prompt_hash_value: str, draw_index: int) -> int:
    if not model_id or not prompt_hash_value:
        raise ProtocolError("screen seed derivation missing an input")
    return domain_int(DOMAIN_SCREEN_GENERATION, SCREEN_ROOT_SEED, STAGE,
                      model_id, prompt_hash_value, draw_index)


@dataclass(frozen=True)
class Constituent:
    role: str          # "A" | "B" | "R1" | "R2" | "R3" | "S1".."S6"
    kind: str          # the constraint family identifier
    severity: int

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.severity}"


@dataclass(frozen=True)
class MatrixCell:
    cell_id: str
    arm: str                       # solo | composed | spanning_solo | spanning_composed
    stem: str
    topic_id: str
    block_index: int
    order_label: str               # "solo" or "<first role>_first"
    constituents: tuple[Constituent, ...]   # in PRESENTATION order
    registered_order: tuple[Constituent, ...]  # in the §8.4 registered order
    wording_indices: tuple[int, ...]        # aligned with constituents
    prompt: str
    prompt_hash: str

    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(c.role for c in self.constituents)


def wording_indices(block_index: int, n_constituents: int) -> tuple[int, ...]:
    """§8.4 verbatim.

    Solo cells use ``i mod 4``. A composed cell uses ``i mod 4`` for the first
    constituent in the REGISTERED order and ``(i + floor(i/4)) mod 4`` for the
    second, applied identically to both order variants of that cell.
    """
    first = block_index % N_WORDINGS
    if n_constituents == 1:
        return (first,)
    second = (block_index + block_index // N_WORDINGS) % N_WORDINGS
    return (first, second)


def spanning_rungs(family: str, ladder: Sequence[int],
                   curve: Mapping[int, float], vacuity: Mapping[int, float],
                   matched_severity: int, matched_compliance: float,
                   *, vacuity_max: float = C.REFERENCE_VACUITY_MAX
                   ) -> list[int]:
    """The V5 arm's two extra severities, by a rule fixed before generation.

    For each target offset, the ladder rung whose calibration solo compliance is
    nearest ``matched_compliance + offset``, among rungs that are not the
    matched rung and that meet the same §13.2 vacuity condition the matched rung
    had to meet. Ties break toward the less restrictive severity.
    """
    chosen: list[int] = []
    for offset in SPANNING_OFFSETS:
        target = matched_compliance + offset
        eligible = [q for q in ladder
                    if q in curve and q != matched_severity and q not in chosen
                    and vacuity.get(q, 1.0) <= vacuity_max]
        if not eligible:
            continue
        chosen.append(min(eligible,
                          key=lambda q: (round(abs(curve[q] - target), 12), -q)))
    return sorted(chosen)


def build_cells(topics: Sequence[Mapping[str, Any]],
                constraints: Sequence[Constituent],
                spanning: Sequence[Constituent],
                *, stem: str, reduced: bool = False,
                class_control: Constituent | None = None) -> list[MatrixCell]:
    """§8.1: five solo cells and ten unordered pairs in both orders, plus the
    V5 spanning arm.

    ``class_control`` adds the production-class companion arm: its solo cell,
    and its composition with **both** outcome constraints in both orders. A is
    the only production constraint in the registered pool and every reference,
    registered or candidate, is a budget, so Delta_R against budgets alone
    cannot separate "A damages B" from "a production companion damages a budget
    outcome". Five extra cells make that separation estimable.

    ``reduced`` builds §8.6 instead: two solo cells and A+B in both orders, the
    design a replication runs when §13.2 admits fewer than three references.
    §13.5 is explicit that this is **not** a terminal status -- D(B<-A),
    D(A<-B) and Lambda need only solo cells and the A+B cell -- so a model that
    fails reference admission still contributes those, and only Delta_R, the
    per-reference quantities and Xi are lost.
    """
    if stem not in STEM_LEVELS:
        raise ProtocolError(f"{stem!r} is not a stem level")
    if reduced:
        if len(constraints) != 2:
            raise ProtocolError("the §8.6 reduced design takes A and B only")
        if spanning:
            raise ProtocolError("the §8.6 reduced design carries no V5 arm: "
                                "with no admitted reference there is no "
                                "companion-difficulty axis to span")
    elif len(constraints) != 5:
        raise ProtocolError("the §8.1 matrix takes exactly five constraints")
    cells: list[MatrixCell] = []

    def add(arm: str, topic, block_index: int,
            registered: tuple[Constituent, ...],
            presentation: tuple[Constituent, ...]):
        if not registered:
            prompt = render(topic["question"], [], stem)
            cells.append(MatrixCell(
                cell_id=f"mx:{topic['topic_id']}:{stem}:none:unconstrained",
                arm=arm, stem=stem, topic_id=topic["topic_id"],
                block_index=block_index, order_label="unconstrained",
                constituents=(), registered_order=(), wording_indices=(),
                prompt=prompt, prompt_hash=prompt_hash(prompt)))
            return
        indices = wording_indices(block_index, len(registered))
        index_by_role = {c.role: i for c, i in zip(registered, indices)}
        lines = [cell_wording(c.kind, index_by_role[c.role], c.severity)
                 for c in presentation]
        prompt = render(topic["question"], lines, stem)
        order_label = ("solo" if len(presentation) == 1
                       else f"{presentation[0].role}_first")
        label = "+".join(c.label for c in presentation)
        cells.append(MatrixCell(
            cell_id=f"mx:{topic['topic_id']}:{stem}:{label}:{order_label}",
            arm=arm, stem=stem, topic_id=topic["topic_id"],
            block_index=block_index, order_label=order_label,
            constituents=presentation, registered_order=registered,
            wording_indices=tuple(index_by_role[c.role] for c in presentation),
            prompt=prompt, prompt_hash=prompt_hash(prompt)))

    for block_index, topic in enumerate(topics):
        # §25: accidental compliance. Every constraint's verifier is evaluated
        # on a prompt that carries no constraint at all, giving the base rate at
        # which an unconstrained answer satisfies it by chance. Without it a
        # "compliance" of 0.7 cannot be read as delivery rather than accident.
        add("unconstrained", topic, block_index, (), ())
        for c in constraints:
            add("solo", topic, block_index, (c,), (c,))
        for first, second in combinations(constraints, 2):
            registered = (first, second)
            add("composed", topic, block_index, registered, (first, second))
            add("composed", topic, block_index, registered, (second, first))
        focal = constraints[1]
        for c in spanning:
            add("spanning_solo", topic, block_index, (c,), (c,))
            # B stated first, so the loss is position-matched to B's solo cell.
            add("spanning_composed", topic, block_index, (focal, c), (focal, c))
        if class_control is not None:
            target = constraints[0]
            add("class_solo", topic, block_index,
                (class_control,), (class_control,))
            for outcome in (focal, target):
                registered = (outcome, class_control)
                add("class_composed", topic, block_index, registered,
                    (outcome, class_control))
                add("class_composed", topic, block_index, registered,
                    (class_control, outcome))
    return cells


def plan_summary(cells: Sequence[MatrixCell]) -> dict[str, Any]:
    by: dict[str, int] = {}
    for c in cells:
        by[c.arm] = by.get(c.arm, 0) + 1
    per_topic = len(cells) // max(1, len({c.topic_id for c in cells}))
    return {"cells": len(cells), "cells_per_block": per_topic,
            "draws_per_cell": DRAWS, "generations": len(cells) * DRAWS,
            "by_arm": by, "blocks": len({c.topic_id for c in cells}),
            "distinct_prompts": len({c.prompt_hash for c in cells})}


def assert_allocation(cells: Sequence[MatrixCell], n_blocks: int) -> dict[str, Any]:
    """§8.4's executable allocation assertion: no structural zero, and both
    orders present for every unordered pair with equal counts."""
    counts: dict[tuple[str, str, str], int] = {}
    wordings: dict[tuple[str, int], int] = {}
    for c in cells:
        key = (c.arm, "|".join(sorted(c.roles)), c.order_label)
        counts[key] = counts.get(key, 0) + 1
        for role, index in zip(c.roles, c.wording_indices):
            wordings[(role, index)] = wordings.get((role, index), 0) + 1
    pairs: dict[tuple[str, str], list[str]] = {}
    for (arm, roles, order), count in counts.items():
        pairs.setdefault((arm, roles), []).append(f"{order}={count}")
    for (arm, roles), entries in pairs.items():
        # The §8.1 matrix and the class-control arm carry both orders of every
        # unordered pair. The V5 spanning arm deliberately carries one -- B
        # stated first, so its loss is position-matched to B's solo cell -- and
        # says so here rather than letting the assertion pass by accident.
        two_orders = arm in ("composed", "class_composed")
        expected_orders = 2 if (two_orders and "|" in roles) else 1
        if len(entries) != expected_orders:
            raise ProtocolError(f"{arm}/{roles} carries {entries}, expected "
                                f"{expected_orders} order(s)")
        got = {int(e.split("=")[1]) for e in entries}
        if got != {n_blocks}:
            raise ProtocolError(f"{arm}/{roles} has counts {got}, expected "
                                f"{n_blocks}")
    for (role, index), count in wordings.items():
        if count == 0:
            raise ProtocolError(f"structural zero: {role} wording {index}")
    return {"cell_types": len(pairs), "blocks": n_blocks,
            "orders_balanced": True,
            "wording_counts": {f"{r}:{i}": n for (r, i), n in sorted(wordings.items())}}


__all__ = ["SCREEN_ROOT_SEED", "DOMAIN_SCREEN_GENERATION", "STAGE", "DRAWS",
           "N_WORDINGS", "SPANNING_OFFSETS", "Constituent", "MatrixCell",
           "screen_seed", "wording_indices", "spanning_rungs", "build_cells",
           "plan_summary", "assert_allocation", "render", "stem_satisfied",
           "STEM_SENTENCE", "STEM_LEVELS"]
