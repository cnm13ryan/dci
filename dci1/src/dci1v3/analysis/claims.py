"""Fixed claim vocabulary and the guarded emitter (§15, §26).

Direction and magnitude are separate interval-based axes. Any string
asserting absence, equivalence, or negligibility is produced only by
``licensed_equivalence``, whose precondition is that the simultaneous
interval lies inside the declared region; reaching it otherwise aborts.
"""
from __future__ import annotations

from typing import Any

from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import (
    EQUIVALENCE_REGION,
    EXCHANGEABILITY_REGION,
    SESOI,
)

DIRECTION_POSITIVE = "positive direction resolved"
DIRECTION_NEGATIVE = "negative direction resolved"
DIRECTION_UNRESOLVED = "direction unresolved"
MAGNITUDE_POSITIVE = "meaningful positive magnitude"
MAGNITUDE_NEGATIVE = "meaningful negative magnitude"
MAGNITUDE_UNRESOLVED = "magnitude unresolved"
EQUIVALENCE = "equivalence"

VOCABULARY = (DIRECTION_POSITIVE, DIRECTION_NEGATIVE, DIRECTION_UNRESOLVED,
              MAGNITUDE_POSITIVE, MAGNITUDE_NEGATIVE, MAGNITUDE_UNRESOLVED,
              EQUIVALENCE)


def licensed_equivalence(interval: tuple[float, float],
                         region: tuple[float, float]) -> str:
    """The single function permitted to emit an equivalence/absence claim."""
    if not (region[0] <= interval[0] and interval[1] <= region[1]):
        raise ProtocolError(
            f"equivalence emitter reached with interval {interval} outside "
            f"region {region}; the analysis aborts")
    return EQUIVALENCE


def primary_claims(interval: tuple[float, float] | None) -> dict[str, Any]:
    """§15 direction and magnitude axes for one primary estimand."""
    if interval is None:
        return {"direction": None, "magnitude": None,
                "status": "INCONCLUSIVE_NO_INTERVAL"}
    low, high = interval
    if low > 0:
        direction = DIRECTION_POSITIVE
    elif high < 0:
        direction = DIRECTION_NEGATIVE
    else:
        direction = DIRECTION_UNRESOLVED
    if low > SESOI:
        magnitude = MAGNITUDE_POSITIVE
    elif high < -SESOI:
        magnitude = MAGNITUDE_NEGATIVE
    elif EQUIVALENCE_REGION[0] <= low and high <= EQUIVALENCE_REGION[1]:
        magnitude = licensed_equivalence((low, high), EQUIVALENCE_REGION)
    else:
        magnitude = MAGNITUDE_UNRESOLVED
    return {"direction": direction, "magnitude": magnitude, "status": "OK"}


def exchangeability_holds(intervals: list[tuple[float, float] | None]
                          ) -> bool | None:
    """Level 2 gate: all three simultaneous intervals inside ±0.05."""
    if any(interval is None for interval in intervals):
        return None
    return all(EXCHANGEABILITY_REGION[0] <= low
               and high <= EXCHANGEABILITY_REGION[1]
               for low, high in intervals)
