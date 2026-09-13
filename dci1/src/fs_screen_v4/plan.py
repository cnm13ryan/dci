"""Cell plan, prompt stem, and the screen's own seed stream.

Seeds are drawn fresh for this screen and separated by domain from every
registered v4 stream, so a screen generation can never collide with a
registered one even at an identical prompt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from dci1v4.design.prompts import prompt_hash
from dci1v4.protocol.hashing import domain_int
from dci1v4.protocol.wordings import wording as registered_wording
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          TARGET_GRID)
from dci1v4.errors import ProtocolError

from fs_screen_v4 import constraints as cc
from fs_screen_v4.wordings import wording as candidate_wording

# --------------------------------------------------------------- seed stream
#: Drawn fresh for this screen. Distinct from every v3 root (202608170-175)
#: and every v4 root (202608190-195).
SCREEN_ROOT_SEED = 202608200
DOMAIN_SCREEN_GENERATION = "fsscreen:gen:v1"

STAGE = "fs-screen"
N_WORDINGS = 4


def screen_seed(model_id: str, prompt_hash_value: str, draw_index: int) -> int:
    if not model_id or not prompt_hash_value:
        raise ProtocolError("screen seed derivation missing an input")
    return domain_int(DOMAIN_SCREEN_GENERATION, SCREEN_ROOT_SEED, STAGE,
                      model_id, prompt_hash_value, draw_index)


# ---------------------------------------------------------------- the stem
#: The STEM factor's only text. One sentence, identical in every cell that
#: carries it, inserted between the topic question and the numbered constraint
#: list. It is background, never an outcome, never in a compliance vector, and
#: never counted toward load.
STEM_SENTENCE = "Answer in 60 to 120 words."
STEM_LEVELS = ("current", "floored")
STEM_TARGET_MIN = 60
STEM_TARGET_MAX = 120


def render(question: str, constraint_lines: Sequence[str], stem: str) -> str:
    """The registered templates, with the stem inserted when stem='floored'."""
    if stem not in STEM_LEVELS:
        raise ProtocolError(f"{stem!r} is not a STEM level")
    head = question if stem == "current" else f"{question}\n\n{STEM_SENTENCE}"
    lines = list(constraint_lines)
    if not lines:
        return f"{head}\n\nAnswer:"
    if len(lines) == 1:
        return f"{head}\n\n1. {lines[0]}\n\nAnswer:"
    if len(lines) == 2:
        return f"{head}\n\n1. {lines[0]}\n2. {lines[1]}\n\nAnswer:"
    raise ProtocolError("a screen prompt carries at most two constraints")


def stem_satisfied(word_count: int) -> bool:
    """Diagnostic only: did the model obey the length instruction?"""
    return STEM_TARGET_MIN <= word_count <= STEM_TARGET_MAX


# ------------------------------------------------------------- the cell plan
@dataclass(frozen=True)
class ScreenCell:
    cell_id: str
    form: str                       # "count" | "candidate" | "outcome"
    stem: str                       # "current" | "floored"
    kind: str
    severity: int
    topic_id: str
    prompt: str
    prompt_hash: str
    companion: tuple[str, int] | None = None


def _reanchor_rungs(family: str) -> list[int]:
    """Two deterministic rungs per registered family, so the count x floored
    cell can re-anchor its own curve rather than borrowing the current one."""
    ladder = REFERENCE_LADDERS[family]
    return sorted({ladder[0], ladder[len(ladder) // 2]})


def count_floored_severities(caliper_rungs: Sequence[str]) -> list[tuple[str, int]]:
    """The registered rungs to re-run under the floored stem.

    ``caliper_rungs`` are the rungs that fell inside the 0.10 caliper for this
    model, read from its registered ``regime_screen.json``. Deterministic given
    that record plus this function.
    """
    chosen: set[tuple[str, int]] = set()
    for rung in caliper_rungs:
        family, severity = rung.split(":")
        chosen.add((family, int(severity)))
    for family in REFERENCE_LADDERS:
        for q in _reanchor_rungs(family):
            chosen.add((family, q))
    return sorted(chosen)


#: The fixture pair reused from §12.1 cap selection, so the floored D(B<-A)
#: baseline is comparable with the one already measured under the current stem.
FIXTURE_A_N = 3
FIXTURE_B_M = 8


def build_cells(topics: Sequence[dict[str, Any]],
                caliper_rungs: Sequence[str]) -> list[ScreenCell]:
    """Every cell this screen generates, in a fixed order.

    ``count x current`` is deliberately absent: it already exists on disk as the
    registered §12.2 ladder screen and is reused rather than regenerated.
    """
    cells: list[ScreenCell] = []

    def add(form, stem, kind, severity, topic, position, *, companion=None,
            wording_fn=None):
        index = position % N_WORDINGS
        if companion is None:
            lines = [wording_fn(kind, index, severity)]
        else:
            ck, cs = companion
            lines = [registered_wording(kind, index, severity),
                     registered_wording(ck, index, cs)]
        prompt = render(topic["question"], lines, stem)
        label = (f"{form}:{stem}:{kind}:{severity}" if companion is None
                 else f"{form}:{stem}:{kind}:{severity}+{companion[0]}:{companion[1]}")
        cells.append(ScreenCell(
            cell_id=f"fs:{topic['topic_id']}:{label}", form=form, stem=stem,
            kind=kind, severity=severity, topic_id=topic["topic_id"],
            prompt=prompt, prompt_hash=prompt_hash(prompt),
            companion=companion))

    candidate = cc.all_severities()
    counts = count_floored_severities(caliper_rungs)

    for position, topic in enumerate(topics):
        offset = 0
        # 1-2. candidate families under both stems
        for stem in STEM_LEVELS:
            for kind, q in candidate:
                add("candidate", stem, kind, q, topic, position + offset,
                    wording_fn=candidate_wording)
                offset += 1
        # 3. registered families under the floored stem only
        for kind, q in counts:
            add("count", "floored", kind, q, topic, position + offset,
                wording_fn=registered_wording)
            offset += 1
        # 4. A and B solo under the floored stem
        for n in TARGET_GRID:
            add("outcome", "floored", "A", n, topic, position + offset,
                wording_fn=registered_wording)
            offset += 1
        for m in FOCAL_GRID:
            add("outcome", "floored", "B", m, topic, position + offset,
                wording_fn=registered_wording)
            offset += 1
        # 5. the A+B fixture pair under the floored stem
        add("outcome", "floored", "A", FIXTURE_A_N, topic, position + offset,
            companion=("B", FIXTURE_B_M))
        offset += 1
    return cells


def plan_summary(cells: Sequence[ScreenCell]) -> dict[str, Any]:
    by: dict[str, int] = {}
    for c in cells:
        by[f"{c.form}:{c.stem}"] = by.get(f"{c.form}:{c.stem}", 0) + 1
    return {"total_generations": len(cells), "by_cell_class": by,
            "distinct_prompts": len({c.prompt_hash for c in cells})}
