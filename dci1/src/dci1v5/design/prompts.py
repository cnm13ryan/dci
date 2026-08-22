"""The §8.5 four-part prompt template.

v4r2's template had three parts: the question, the numbered constraint list,
and ``Answer:``. v4r3 inserts the answer-length sentence between the first two,
byte-identically in every cell without exception -- unconstrained, solo and
composed, in both orders, on every model.

The stem is background. It is never scored, never enters a compliance vector,
never counts toward load, has no severity, ladder, wording or witness
obligation, and is not subject to the §7.5 caliper. Its realised satisfaction
rate is a per-load diagnostic and gates nothing.
"""
from __future__ import annotations

from typing import Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_text

from dci1v5.protocol import constants as C

__all__ = ["STEM_SENTENCE", "render", "prompt_hash", "stem_satisfied",
           "assert_stem_present", "assert_shared_constituent_identity"]

STEM_SENTENCE = C.STEM_SENTENCE


def render(question: str, constraint_lines: Sequence[str]) -> str:
    """The registered template. Load is 0, 1 or 2 (§1, §8.1)."""
    lines = list(constraint_lines)
    if not lines:
        return C.PROMPT_ZERO.format(question=question)
    if len(lines) == 1:
        return C.PROMPT_ONE.format(question=question, c1=lines[0])
    if len(lines) == 2:
        return C.PROMPT_TWO.format(question=question, c1=lines[0], c2=lines[1])
    raise ProtocolError("a v4r3 prompt carries at most two constraints "
                        "(load is fixed at 0, 1 or 2, §1)")


def prompt_hash(prompt: str) -> str:
    return sha_text(prompt)


def stem_satisfied(word_count: int) -> bool:
    """§8.5's diagnostic. Gates nothing and no estimand reads it."""
    low, high = C.STEM_BAND
    return low <= word_count <= high


def assert_stem_present(prompt: str) -> None:
    """§8.5: the stem is in every prompt, byte for byte.

    On the mandatory path because the whole v4r2 -> v4r3 regime change rests
    on it: a cell rendered without the stem is not comparable with any other
    cell in the study, and the failure would be silent.
    """
    if prompt.count(STEM_SENTENCE) != 1:
        raise ProtocolError(
            "§8.5 requires the answer-length sentence exactly once in every "
            f"prompt; this one carries it {prompt.count(STEM_SENTENCE)} times")


def assert_shared_constituent_identity(prompts: dict[str, str],
                                       lines: dict[str, tuple[str, str]]
                                       ) -> None:
    """§8.5: two composed prompts sharing a constituent differ only in the
    line stating the other one."""
    skeletons: dict[tuple[str, int], set[str]] = {}
    for key, prompt in prompts.items():
        first, second = lines[key]
        skeletons.setdefault((first, 1), set()).add(
            prompt.replace(second, "<OTHER>"))
        skeletons.setdefault((second, 2), set()).add(
            prompt.replace(first, "<OTHER>"))
    for (line, position), variants in sorted(skeletons.items()):
        if len(variants) > 1:
            raise ProtocolError(
                f"prompts sharing the constituent {line!r} in position "
                f"{position} differ outside the other constituent's line")
