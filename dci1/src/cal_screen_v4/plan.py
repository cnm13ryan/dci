"""Cells, prompts and the screen's own seed stream.

The stem and the extended focal grid are *imported* from the two screens that
established them rather than restated, so a byte difference cannot make the
three screens non-comparable. ``assert_inherited_definitions`` pins that.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.design.prompts import prompt_hash
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import domain_int
from dci1v4.protocol.wordings import wording as registered_wording
from dci1v4.verifiers.constraints import REFERENCE_LADDERS, TARGET_GRID

from bgrid_screen_v4 import focal
from fs_screen_v4.constraints import CANDIDATES
from fs_screen_v4.plan import (STEM_LEVELS, STEM_SENTENCE, STEM_TARGET_MAX,
                               STEM_TARGET_MIN, render, stem_satisfied)
from fs_screen_v4.wordings import wording as candidate_wording

# --------------------------------------------------------------- seed stream
#: Drawn fresh. Distinct from every v3 root (202608170-175), every v4 root
#: (202608190-195), the FORM x STEM root (202608200) and the B-grid root
#: (202608210).
SCREEN_ROOT_SEED = 202608220
DOMAIN_SCREEN_GENERATION = "calscreen:gen:v1"
STAGE = "cal-screen"
N_WORDINGS = 4

#: §12.3 and §13.2 measure at M_cal = 4 on the 96 solo-calibration topics.
#: Both are registered values, imported below in ``assert_inherited_definitions``.
DRAWS = 4

#: The three rate families Amendment B §6 recommends in advance and the FORM x
#: STEM screen supports. The lower-bound families are deliberately absent: a
#: lower bound imposes a length *floor*, pushing length up while B pushes it
#: down, which replaces one length confound with its mirror image.
CANDIDATE_FAMILIES: tuple[str, ...] = ("CR7", "CR4", "CR6")

#: How many registered-pool rungs are carried as the control arm. The registered
#: pool's failure is structural and already established 0-of-64; this arm exists
#: so the candidate result is a *comparison* on the calibration set rather than
#: an assertion about it.
REGISTERED_CONTROL_RUNGS = 4


def screen_seed(model_id: str, prompt_hash_value: str, draw_index: int) -> int:
    if not model_id or not prompt_hash_value:
        raise ProtocolError("screen seed derivation missing an input")
    return domain_int(DOMAIN_SCREEN_GENERATION, SCREEN_ROOT_SEED, STAGE,
                      model_id, prompt_hash_value, draw_index)


def assert_inherited_definitions() -> dict[str, Any]:
    """Nothing measured here may drift from what the earlier screens measured."""
    from dci1v4.protocol import constants as C

    if STEM_SENTENCE != "Answer in 60 to 120 words.":
        raise ProtocolError("the inherited stem sentence has changed")
    if focal.SCREEN_FOCAL_GRID != (7, 8, 9, 10, 11, 12):
        raise ProtocolError("the inherited extended focal grid has changed")
    if DRAWS != C.M_CAL:
        raise ProtocolError(f"screen draws {DRAWS} != registered M_cal "
                            f"{C.M_CAL}")
    for family in CANDIDATE_FAMILIES:
        if family not in CANDIDATES:
            raise ProtocolError(f"{family} is not a screened candidate family")
        if CANDIDATES[family].form != "rate":
            raise ProtocolError(f"{family} is not a rate family")
    return {
        "stem_sentence": STEM_SENTENCE,
        "stem_levels": list(STEM_LEVELS),
        "stem_imported_from": "fs_screen_v4.plan",
        "extended_focal_grid": list(focal.SCREEN_FOCAL_GRID),
        "focal_grid_imported_from": "bgrid_screen_v4.focal",
        "draws_per_cell": DRAWS,
        "m_cal": C.M_CAL,
        "candidate_families": list(CANDIDATE_FAMILIES),
        "candidate_ladders": {f: list(CANDIDATES[f].ladder)
                              for f in CANDIDATE_FAMILIES},
    }


# ------------------------------------------------------- the control arm rule
def registered_control_rungs(prescreen_curves: Mapping[str, Mapping[str, float]],
                             a_prescreen: float) -> list[tuple[str, int]]:
    """The registered-pool control arm, chosen by a rule fixed before generation.

    One rung per family, from the families whose best rung is nearest A's
    pre-screen solo compliance **measured under the same stem the control arm
    is generated under**, ties broken by family identifier then by the less
    restrictive severity.

    The stem matters and the honest choice is the one that gives the registered
    pool its best shot: picking rungs by their proximity to A under the current
    stem and then generating them under the floored stem would stack the
    comparison against the pool this arm exists to represent fairly.
    """
    best: list[tuple[float, str, int]] = []
    for family, curve in sorted(prescreen_curves.items()):
        if family not in REFERENCE_LADDERS:
            continue
        rungs = [(abs(float(v) - a_prescreen), -int(q), int(q))
                 for q, v in curve.items() if int(q) in REFERENCE_LADDERS[family]]
        if not rungs:
            continue
        distance, _, severity = min(rungs)
        best.append((distance, family, severity))
    best.sort(key=lambda item: (round(item[0], 12), item[1], -item[2]))
    return [(family, severity) for _, family, severity in
            best[:REGISTERED_CONTROL_RUNGS]]


# ------------------------------------------------------------- the cell plan
@dataclass(frozen=True)
class ScreenCell:
    cell_id: str
    arm: str                 # a_solo | b_solo | candidate | registered_control
    stem: str                # "current" | "floored"
    kind: str
    severity: int
    topic_id: str
    prompt: str
    prompt_hash: str
    wording_index: int


def cell_wording(kind: str, index: int, severity: int) -> str:
    """Registered wordings where they exist; the screens' own renderers where
    the registered code correctly refuses an unregistered symbol."""
    if kind in CANDIDATES:
        return candidate_wording(kind, index, severity)
    if kind == "B" and severity not in (7, 8, 9, 10):
        return focal.screen_wording(severity, index)
    return registered_wording(kind, index, severity)


def build_cells(topics: Sequence[Mapping[str, Any]],
                control_rungs: Sequence[tuple[str, int]]) -> list[ScreenCell]:
    """Every cell this screen generates, in a fixed order.

    Solo cells only. Wording allocation is the registered §8.4 solo rule --
    index ``i mod 4`` at block index ``i`` -- so the four wordings are exactly
    balanced across the 96 topics for every cell type.
    """
    cells: list[ScreenCell] = []

    def add(arm: str, stem: str, kind: str, severity: int, topic, index: int):
        line = cell_wording(kind, index, severity)
        prompt = render(topic["question"], [line], stem)
        cells.append(ScreenCell(
            cell_id=f"cal:{topic['topic_id']}:{stem}:{kind}:{severity}",
            arm=arm, stem=stem, kind=kind, severity=severity,
            topic_id=topic["topic_id"], prompt=prompt,
            prompt_hash=prompt_hash(prompt), wording_index=index))

    for position, topic in enumerate(topics):
        index = position % N_WORDINGS
        for n in TARGET_GRID:
            add("a_solo", "floored", "A", n, topic, index)
        for m in focal.SCREEN_FOCAL_GRID:
            add("b_solo", "floored", "B", m, topic, index)
        for m in focal.SCREEN_FOCAL_GRID:
            add("b_solo", "current", "B", m, topic, index)
        for family in CANDIDATE_FAMILIES:
            for q in CANDIDATES[family].ladder:
                add("candidate", "floored", family, q, topic, index)
        for family, q in control_rungs:
            add("registered_control", "floored", family, q, topic, index)
    return cells


def plan_summary(cells: Sequence[ScreenCell]) -> dict[str, Any]:
    by: dict[str, int] = {}
    for c in cells:
        key = f"{c.arm}:{c.stem}"
        by[key] = by.get(key, 0) + 1
    return {"cells": len(cells), "draws_per_cell": DRAWS,
            "generations": len(cells) * DRAWS,
            "by_arm": by,
            "distinct_prompts": len({c.prompt_hash for c in cells})}


__all__ = ["SCREEN_ROOT_SEED", "DOMAIN_SCREEN_GENERATION", "STAGE", "DRAWS",
           "N_WORDINGS", "CANDIDATE_FAMILIES", "REGISTERED_CONTROL_RUNGS",
           "ScreenCell", "screen_seed", "assert_inherited_definitions",
           "registered_control_rungs", "cell_wording", "build_cells",
           "plan_summary", "render", "stem_satisfied", "STEM_SENTENCE",
           "STEM_LEVELS", "STEM_TARGET_MIN", "STEM_TARGET_MAX"]
