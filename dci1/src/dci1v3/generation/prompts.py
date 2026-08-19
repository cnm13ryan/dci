"""Prompt construction and prompt plans (§7).

Every prompt is the topic question, a numbered list of the active
constraints, and ``Answer:``, in that order. Within a block, compared
prompts are byte-identical outside the added-constraint line, asserted
executably. Every generative stage carries a prompt plan (cell identities,
prompt hashes, draw counts) and an allocation coverage assertion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dci1v3.errors import ProtocolError
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_text
from dci1v3.protocol.wordings import wording
from dci1v3.topics.split import Block


@dataclass(frozen=True)
class Cell:
    """One logical prompt cell of one stage."""

    cell_id: str
    stage: str                     # pilot | prescreen | gate1 | gate2a | ...
    topic_id: str
    block_id: str | None
    arm: str | None                # AB/AR1/AR2/AR3/A/TOPIC for arm stages
    kind: str                      # e.g. "arm:AB" or "solo:A:n=3"
    constraint_id: str | None      # added/solo constraint identity
    severity: int | None
    order: str | None
    target_wording: int | None
    added_wording: int | None
    n: int | None
    prompt: str
    prompt_hash: str
    draws: int
    active_wordings: tuple[str, ...] = ()


def _prompt(question: str, constraints: list[str]) -> str:
    if len(constraints) == 2:
        return C.PROMPT_TWO.format(question=question, c1=constraints[0],
                                   c2=constraints[1])
    if len(constraints) == 1:
        return C.PROMPT_ONE.format(question=question, c1=constraints[0])
    if not constraints:
        return C.PROMPT_ZERO.format(question=question)
    raise ProtocolError("a prompt carries at most two constraints")


def _cell(stage: str, topic_id: str, prompt: str, *, draws: int,
          **fields: Any) -> Cell:
    kind = fields.pop("kind")
    cell_id = f"{stage}:{topic_id}:{kind}"
    return Cell(cell_id=cell_id, stage=stage, topic_id=topic_id,
                prompt=prompt, prompt_hash=sha_text(prompt), draws=draws,
                kind=kind, **{
                    "block_id": None, "arm": None, "constraint_id": None,
                    "severity": None, "order": None, "target_wording": None,
                    "added_wording": None, "n": None,
                    "active_wordings": (), **fields})


def arm_cells(stage: str, blocks: list[Block], *, n: int, m: int,
              references: tuple[tuple[str, int], ...], draws: int
              ) -> list[Cell]:
    """Six-arm cells for pilot or confirmatory blocks; §7 byte-identity
    asserted per block."""
    if len(references) != C.N_FINAL_REFERENCES:
        raise ProtocolError("exactly three references are required")
    cells: list[Cell] = []
    for block in blocks:
        target_text = wording("A", block.target_wording, n=n)
        added: dict[str, tuple[str, str, int]] = {
            "AB": ("B", wording("B", block.added_wording, m=m), m)}
        for index, (family, q) in enumerate(references, start=1):
            added[f"AR{index}"] = (
                family, wording(family, block.added_wording, q=q), q)
        block_prompts: dict[str, str] = {}
        for arm in C.ARMS:
            if arm in added:
                constraint_id, added_text, severity = added[arm]
                pair = ([target_text, added_text]
                        if block.order == C.TARGET_FIRST
                        else [added_text, target_text])
                prompt = _prompt(block.question, pair)
                active = (target_text, added_text)
            elif arm == "A":
                constraint_id, severity = None, None
                prompt = _prompt(block.question, [target_text])
                active = (target_text,)
            else:
                constraint_id, severity = None, None
                prompt = _prompt(block.question, [])
                active = ()
            block_prompts[arm] = prompt
            cells.append(_cell(
                stage, block.topic_id, prompt, draws=draws,
                kind=f"arm:{arm}", block_id=block.block_id, arm=arm,
                constraint_id=constraint_id, severity=severity,
                order=block.order, target_wording=block.target_wording,
                added_wording=block.added_wording, n=n,
                active_wordings=active))
        _assert_block_byte_identity(block_prompts, added)
    return cells


def _assert_block_byte_identity(prompts: dict[str, str],
                                added: dict[str, tuple[str, str, int]]
                                ) -> None:
    """§7: compared prompts differ only in the added-constraint line."""
    reference = prompts["AB"].replace(added["AB"][1], "{ADDED}")
    for arm in ("AR1", "AR2", "AR3"):
        candidate = prompts[arm].replace(added[arm][1], "{ADDED}")
        if candidate != reference:
            raise ProtocolError(
                f"{arm} prompt differs from AB outside the added-constraint "
                f"line")


def solo_cells(stage: str, topics: list[dict[str, Any]],
               kinds: list[tuple[str, int]], *, draws: int) -> list[Cell]:
    """Single-constraint cells: one prompt per (topic, constraint, severity),
    wording (topic_position + severity_position) mod 4 (registered
    allocation; coverage asserted)."""
    cells: list[Cell] = []
    for position, topic in enumerate(topics):
        for severity_position, (constraint_id, severity) in enumerate(kinds):
            windex = (position + severity_position) % 4
            if constraint_id == "A":
                text = wording("A", windex, n=severity)
            elif constraint_id == "B":
                text = wording("B", windex, m=severity)
            else:
                text = wording(constraint_id, windex, q=severity)
            prompt = _prompt(topic["question"], [text])
            is_target = constraint_id == "A"
            cells.append(_cell(
                stage, topic["topic_id"], prompt, draws=draws,
                kind=f"solo:{constraint_id}:{severity}",
                constraint_id=None if is_target else constraint_id,
                severity=None if is_target else severity,
                target_wording=windex if is_target else None,
                added_wording=None if is_target else windex,
                n=severity if is_target else None,
                active_wordings=(text,)))
    assert_solo_coverage(cells, topics=len(topics), kinds=len(kinds))
    return cells


def composed_cells(stage: str, topics: list[dict[str, Any]], *, n: int,
                   family: str, q: int, draws: int) -> list[Cell]:
    """A+R_f cells on the composed-validation set; order p mod 2, target
    wording p mod 4, added wording (p + p//4) mod 4."""
    cells: list[Cell] = []
    for position, topic in enumerate(topics):
        order = C.TARGET_FIRST if position % 2 == 0 else C.ADDED_FIRST
        target_windex = position % 4
        added_windex = (position + position // 4) % 4
        target_text = wording("A", target_windex, n=n)
        added_text = wording(family, added_windex, q=q)
        pair = ([target_text, added_text] if order == C.TARGET_FIRST
                else [added_text, target_text])
        prompt = _prompt(topic["question"], pair)
        cells.append(_cell(
            stage, topic["topic_id"], prompt, draws=draws,
            kind=f"composed:{family}:{q}", constraint_id=family,
            severity=q, order=order, target_wording=target_windex,
            added_wording=added_windex, n=n,
            active_wordings=(target_text, added_text)))
    return cells


def assert_solo_coverage(cells: list[Cell], *, topics: int, kinds: int
                         ) -> None:
    """§7 allocation assertion for solo stages: with topics divisible by
    four, every wording index appears topics/4 times within each kind."""
    if len(cells) != topics * kinds:
        raise ProtocolError(f"{len(cells)} solo cells, expected "
                            f"{topics * kinds}")
    if topics % 4:
        raise ProtocolError("solo stages require topic counts divisible "
                            "by four")
    per: dict[tuple[str, int], int] = {}
    for cell in cells:
        windex = (cell.target_wording if cell.constraint_id is None
                  else cell.added_wording)
        per[(cell.kind, windex)] = per.get((cell.kind, windex), 0) + 1
    for (kind, windex), count in per.items():
        if count != topics // 4:
            raise ProtocolError(
                f"solo wording allocation unbalanced: {kind} wording "
                f"{windex} appears {count} times, expected {topics // 4}")


def prompt_plan(cells: list[Cell]) -> dict[str, Any]:
    """The frozen prompt plan for one stage."""
    ids = [c.cell_id for c in cells]
    if len(set(ids)) != len(ids):
        raise ProtocolError("duplicate cell identities in prompt plan")
    return {"cells": [{
        "cell_id": c.cell_id, "stage": c.stage, "topic_id": c.topic_id,
        "block_id": c.block_id, "arm": c.arm, "kind": c.kind,
        "constraint_id": c.constraint_id, "severity": c.severity,
        "order": c.order, "target_wording": c.target_wording,
        "added_wording": c.added_wording, "n": c.n,
        "prompt_hash": c.prompt_hash, "draws": c.draws} for c in cells]}
