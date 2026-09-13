"""Prompt construction (v4r2 §8.5).

Every prompt has three parts in the same order: the topic question, a numbered
list of the active constraints, and the line ``Answer:``. Both constraints
occupy the same authority level in the same numbered list in the same user
message, and no constraint is ever placed in a system message.

Within a block, two composed prompts sharing a constituent differ byte for
byte only in the line stating the other constituent — asserted executably by
``assert_shared_constituent_identity`` rather than trusted to the template.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.hashing import sha_text


def render(question: str, constraint_lines: list[str]) -> str:
    if len(constraint_lines) == 2:
        return C.PROMPT_TWO.format(question=question, c1=constraint_lines[0],
                                   c2=constraint_lines[1])
    if len(constraint_lines) == 1:
        return C.PROMPT_ONE.format(question=question, c1=constraint_lines[0])
    if not constraint_lines:
        return C.PROMPT_ZERO.format(question=question)
    raise ProtocolError("a v4 prompt carries at most two constraints "
                        "(load is fixed at one or two, §1)")


def prompt_hash(prompt: str) -> str:
    return sha_text(prompt)


def assert_shared_constituent_identity(prompts: dict[str, str],
                                       lines: dict[str, tuple[str, str]]
                                       ) -> None:
    """§8.5: two composed prompts sharing a constituent differ only in the
    line stating the other one.

    ``prompts`` maps a cell key to its rendered prompt; ``lines`` maps the same
    key to its two constraint lines in prompt order. The check substitutes each
    line with a placeholder and requires the remainder to be identical across
    every cell that shares a constituent in the same position.
    """
    skeletons: dict[tuple[str, int], set[str]] = {}
    for key, prompt in prompts.items():
        first, second = lines[key]
        skeletons.setdefault((first, 1), set()).add(
            prompt.replace(second, "{OTHER}"))
        skeletons.setdefault((second, 2), set()).add(
            prompt.replace(first, "{OTHER}"))
    for (line, position), variants in skeletons.items():
        if len(variants) > 1:
            raise ProtocolError(
                f"prompts sharing the constituent {line!r} in position "
                f"{position} differ outside the other constituent's line")
