"""Realised discordance, achieved detectable effects, uninformative topics
(prereg §13). Reported beside every estimate; never used to change a rule."""
from __future__ import annotations

import math
from typing import Any

from dci1.protocol.constants import ARMS

#: (z_{0.975} + z_{0.8})^2 for a single paired binary contrast (§13).
MARGINAL_COEFFICIENT = 7.84


def discordance(column: list[float]) -> float:
    """Proportion of blocks whose paired quantity is non-zero."""
    if not column:
        return float("nan")
    return sum(1 for v in column if v != 0) / len(column)


def marginal_detectable(p_d: float, blocks: int) -> float:
    if blocks <= 0 or p_d < 0:
        return float("nan")
    return math.sqrt(MARGINAL_COEFFICIENT * p_d / blocks)


def simultaneous_detectable(p_d: float, blocks: int,
                            critical_value: float | None) -> float:
    """Substitutes (c + 0.84)^2 for 7.84, with c the family's realised
    bootstrap critical value (§13)."""
    if critical_value is None or blocks <= 0:
        return float("nan")
    return math.sqrt((critical_value + 0.84) ** 2 * p_d / blocks)


def uninformative_share(blocks: dict[str, dict[str, Any]]) -> float:
    """Topics whose S0 verdicts are identical in every arm (§10, §13)."""
    if not blocks:
        return float("nan")
    flat = 0
    for entry in blocks.values():
        verdicts = {entry["arms"][arm]["f_s0"] for arm in ARMS}
        if len(verdicts) == 1:
            flat += 1
    return flat / len(blocks)
