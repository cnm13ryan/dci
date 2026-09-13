"""v4r3's topic sets: v4r2's split, carried and re-checked (§6.2).

v4r3 registers the same five-way cut as v4r2 -- 2 pre-screen, 8 solo, 2
composed validation, 32 confirmatory and 8 sequestered per area -- so the
split is not re-derived here. ``split_topics`` is v4r2's function on v4r2's
seed, and this module's only job is to assert that the counts it returns are
the counts v4r3 registers, so a divergence is a refusal rather than a silent
re-cut.

An earlier v4r3 draft registered 34 confirmatory and 6 sequestered per area to
reach 408 blocks. That cut is not executable: the released bank holds the 528
non-sequestered questions and the other 96 exist to this repository only as
opaque identities and content hashes, so the two extra confirmatory topics per
area could only come from text no v4-era process can read. §16.2 reaches the
same precision preconditions by raising M instead.
"""
from __future__ import annotations

from typing import Any

from dci1v4.errors import ProtocolError
from dci1v4.protocol.seeds import TOPIC_SPLIT_SEED
from dci1v4.topics.split import split_topics as _v4_split_topics

from dci1v4r3.protocol import constants as C
from dci1v4r3.protocol.seeds import CARRIED_TOPIC_SPLIT_SEED

__all__ = ["split_topics", "assert_split_is_v4r2s"]


def assert_split_is_v4r2s() -> None:
    if TOPIC_SPLIT_SEED != CARRIED_TOPIC_SPLIT_SEED:
        raise ProtocolError(
            "§6.2 carries v4r2's topic split, so the split seed must be "
            f"v4r2's {CARRIED_TOPIC_SPLIT_SEED}; it is {TOPIC_SPLIT_SEED}")


def split_topics() -> dict[str, list[dict[str, Any]]]:
    """The five registered sets, with v4r3's counts asserted."""
    assert_split_is_v4r2s()
    sets = _v4_split_topics()
    for name, expected in C.SET_SIZES.items():
        if name == "sequestered":
            continue
        got = len(sets.get(name, ()))
        if got != expected:
            raise ProtocolError(
                f"§6.2 registers {expected} {name} topics; the carried split "
                f"returns {got}. v4r3 does not re-cut the bank, so a "
                "mismatch is a defect in one of the two documents")
    return sets
