"""Exact prompt construction (prereg §7; decision D12).

Every prompt is exactly three parts in this order: the topic question, a
numbered list of the active constraints, and the line ``Answer:``. Within a
block, the prompts of the focal arm and each reference arm are byte-identical
except for the single line stating the added constraint. No system message
exists; both constraints share one numbered list in one user turn (§7).
"""
from __future__ import annotations

from dci1.constraints.wordings import wording
from dci1.design.blocks import TARGET_FIRST, Block
from dci1.protocol.constants import ARMS, PRIMARY_ARMS, ProtocolError
from dci1.protocol.hashing import sha_text


def compose(question: str, constraint_lines: tuple[str, ...]) -> str:
    """The exact prompt bytes (D12)."""
    if constraint_lines:
        numbered = "\n".join(f"{i + 1}. {text}"
                             for i, text in enumerate(constraint_lines))
        return f"{question}\n\n{numbered}\n\nAnswer:"
    return f"{question}\n\nAnswer:"


def added_constraint_id(arm: str, references: tuple[str, str, str]) -> str | None:
    """Which constraint occupies the added slot in this arm."""
    if arm == "focal":
        return "B"
    if arm in ("ref1", "ref2", "ref3"):
        return references[int(arm[3]) - 1]
    if arm in ("target_alone", "topic_alone"):
        return None
    raise ProtocolError(f"unknown arm {arm!r}")


def prompt_for_cell(block: Block, arm: str, *, n: int, m: int,
                    references: tuple[str, str, str]) -> str:
    """The exact prompt for one (block, arm) cell."""
    if arm not in ARMS:
        raise ProtocolError(f"unknown arm {arm!r}")
    target_text = wording("A", block.wording_target, n=n)
    if arm == "topic_alone":
        return compose(block.question, ())
    if arm == "target_alone":
        return compose(block.question, (target_text,))
    added_id = added_constraint_id(arm, references)
    added_text = wording(added_id, block.wording_added,
                         m=m if added_id == "B" else None)
    if block.order == TARGET_FIRST:
        lines = (target_text, added_text)
    else:
        lines = (added_text, target_text)
    return compose(block.question, lines)


def prompt_hash(prompt: str) -> str:
    return sha_text(prompt)


def constraint_block_text(block: Block, arm: str, *, n: int, m: int,
                          references: tuple[str, str, str]) -> tuple[str, ...]:
    """The active constraint wordings of a cell, for S3 and the taxonomy."""
    target_text = wording("A", block.wording_target, n=n)
    if arm == "topic_alone":
        return ()
    if arm == "target_alone":
        return (target_text,)
    added_id = added_constraint_id(arm, references)
    added_text = wording(added_id, block.wording_added,
                         m=m if added_id == "B" else None)
    return ((target_text, added_text) if block.order == TARGET_FIRST
            else (added_text, target_text))


def assert_matched_arm_byte_identity(block: Block, *, n: int, m: int,
                                     references: tuple[str, str, str]) -> None:
    """§7: matched arms differ only in the single added-constraint line."""
    prompts = {arm: prompt_for_cell(block, arm, n=n, m=m,
                                    references=references)
               for arm in PRIMARY_ARMS}
    added_line_index = 1 if block.order == TARGET_FIRST else 0
    reference_lines = None
    for arm, text in prompts.items():
        lines = text.split("\n")
        # Remove the numbered added-constraint line; the rest must be identical
        # byte for byte across the four matched arms.
        del lines[2 + added_line_index]
        if reference_lines is None:
            reference_lines = lines
        elif lines != reference_lines:
            raise ProtocolError(
                f"block {block.block_id}: arms differ outside the added line")
