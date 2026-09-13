"""Cells, prompts and the screen's own seed stream.

The stem is imported from ``fs_screen_v4`` rather than restated: the B-grid
screen measures the focal curve *under the stem the FORM x STEM screen tested*,
so a byte difference between the two would make the two screens
non-comparable. ``assert_stem_identical`` pins that.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from dci1v4.design.prompts import prompt_hash
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import domain_int
from dci1v4.protocol.wordings import wording as registered_wording
from dci1v4.verifiers.constraints import TARGET_GRID

from bgrid_screen_v4 import focal
from fs_screen_v4.plan import (STEM_LEVELS, STEM_SENTENCE, STEM_TARGET_MAX,
                               STEM_TARGET_MIN, render, stem_satisfied)

# --------------------------------------------------------------- seed stream
#: Drawn fresh. Distinct from every v3 root (202608170-175), every v4 root
#: (202608190-195) and the FORM x STEM screen root (202608200).
SCREEN_ROOT_SEED = 202608210
DOMAIN_SCREEN_GENERATION = "bgrid:gen:v1"
STAGE = "bgrid-screen"
N_WORDINGS = 4


def screen_seed(model_id: str, prompt_hash_value: str, draw_index: int) -> int:
    if not model_id or not prompt_hash_value:
        raise ProtocolError("screen seed derivation missing an input")
    return domain_int(DOMAIN_SCREEN_GENERATION, SCREEN_ROOT_SEED, STAGE,
                      model_id, prompt_hash_value, draw_index)


def assert_stem_identical() -> dict:
    if STEM_SENTENCE != "Answer in 60 to 120 words.":
        raise ProtocolError("the screened stem sentence has changed")
    return {"stem_sentence": STEM_SENTENCE,
            "imported_from": "fs_screen_v4.plan",
            "levels": list(STEM_LEVELS),
            "diagnostic_window": [STEM_TARGET_MIN, STEM_TARGET_MAX]}


# ------------------------------------------------------------- the cell plan
#: A's severity in the composed fixture. The §12.1 cap set and the FORM x STEM
#: screen both used (A=3, B=8), so A=3 keeps the D(B<-A) baselines comparable.
FIXTURE_A_N = 3

#: B solo under the CURRENT stem is regenerated only at the two screen rungs;
#: m = 7 to 10 already exist as the registered §12.2 ladder screen and are read
#: from disk without regeneration.
CURRENT_STEM_RUNGS: tuple[int, ...] = focal.EXTENSION


@dataclass(frozen=True)
class ScreenCell:
    cell_id: str
    stem: str                        # "current" | "floored"
    kind: str                        # "A" | "B"
    severity: int
    topic_id: str
    prompt: str
    prompt_hash: str
    companion: tuple[str, int] | None = None
    role: str = ""                   # b_solo | a_solo | fixture


def _wording(kind: str, index: int, severity: int) -> str:
    """Registered wordings everywhere they exist; the screen renderer only for
    the two extension rungs, which render from the same four templates."""
    if kind == "B" and severity not in (7, 8, 9, 10):
        return focal.screen_wording(severity, index)
    return registered_wording(kind, index, severity)


def build_cells(topics: Sequence[dict[str, Any]]) -> list[ScreenCell]:
    """Every cell this screen generates, in a fixed order.

    The A+B fixture is generated at *every* screen rung rather than only at the
    in-band ones. Which m is in band is not known until the B-solo curve exists,
    and a two-phase run would cost a second engine load per model for no
    scientific gain; the out-of-band fixture rows are reported but carry no
    weight in the §1.4 verdict.
    """
    cells: list[ScreenCell] = []

    def add(stem, kind, severity, topic, position, *, role, companion=None):
        index = position % N_WORDINGS
        lines = [_wording(kind, index, severity)]
        if companion is not None:
            lines.append(_wording(companion[0], index, companion[1]))
        prompt = render(topic["question"], lines, stem)
        label = (f"{stem}:{kind}:{severity}" if companion is None
                 else f"{stem}:{kind}:{severity}+{companion[0]}:{companion[1]}")
        cells.append(ScreenCell(
            cell_id=f"bg:{topic['topic_id']}:{label}", stem=stem, kind=kind,
            severity=severity, topic_id=topic["topic_id"], prompt=prompt,
            prompt_hash=prompt_hash(prompt), companion=companion, role=role))

    for position, topic in enumerate(topics):
        offset = 0
        for m in focal.SCREEN_FOCAL_GRID:          # B solo, floored, 6 rungs
            add("floored", "B", m, topic, position + offset, role="b_solo")
            offset += 1
        for m in CURRENT_STEM_RUNGS:               # B solo, current, 2 rungs
            add("current", "B", m, topic, position + offset, role="b_solo")
            offset += 1
        for n in TARGET_GRID:                      # A solo, floored, 8 rungs
            add("floored", "A", n, topic, position + offset, role="a_solo")
            offset += 1
        for m in focal.SCREEN_FOCAL_GRID:          # A+B fixture, floored
            add("floored", "A", FIXTURE_A_N, topic, position + offset,
                role="fixture", companion=("B", m))
            offset += 1
    return cells


def plan_summary(cells: Sequence[ScreenCell]) -> dict[str, Any]:
    by: dict[str, int] = {}
    for c in cells:
        by[f"{c.role}:{c.stem}"] = by.get(f"{c.role}:{c.stem}", 0) + 1
    return {"total_generations": len(cells), "by_cell_class": by,
            "distinct_prompts": len({c.prompt_hash for c in cells})}


__all__ = ["SCREEN_ROOT_SEED", "DOMAIN_SCREEN_GENERATION", "STAGE",
           "N_WORDINGS", "FIXTURE_A_N", "CURRENT_STEM_RUNGS", "ScreenCell",
           "screen_seed", "assert_stem_identical", "build_cells",
           "plan_summary", "render", "stem_satisfied", "STEM_SENTENCE",
           "STEM_LEVELS", "STEM_TARGET_MIN", "STEM_TARGET_MAX"]
