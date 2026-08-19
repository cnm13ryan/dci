"""Claim rules with a guarded vocabulary (prereg §15, §26).

Any string asserting absence, equivalence or negligibility is produced by
exactly one function, `guarded_absence_claim`, whose precondition is that the
simultaneous interval lies wholly inside the declared region; reaching it with
the precondition false aborts the analysis (§15's executable check).
"""
from __future__ import annotations

from typing import Any

from dci1.protocol.constants import (
    EQUIVALENCE_REGION_EXCHANGEABILITY,
    EQUIVALENCE_REGION_PRIMARY,
    SMALLEST_EFFECT_OF_INTEREST,
    ProtocolError,
)

#: The fixed §15 wordings. Nothing else may assert an outcome.
WORDING_EFFECT = ("The focal constraint changed target failure by the "
                  "estimated amount under the registered conditions")
WORDING_EQUIVALENCE = ("Any effect present is smaller than the smallest "
                       "effect of interest under the registered conditions")
WORDING_UNRESOLVED = ("The study does not resolve this quantity")


def interval_inside(interval: list[float], region: tuple[float, float]) -> bool:
    return region[0] <= interval[0] and interval[1] <= region[1]


def interval_excludes_zero(interval: list[float]) -> bool:
    return interval[0] > 0.0 or interval[1] < 0.0


def guarded_absence_claim(member: str, interval: list[float],
                          region: tuple[float, float]) -> str:
    """THE single producer of absence/equivalence claims. Aborts otherwise."""
    if not interval_inside(interval, region):
        raise ProtocolError(
            f"absence claim reached for {member} with simultaneous interval "
            f"{interval} not inside {region} — the analysis aborts (§15)")
    return WORDING_EQUIVALENCE


def primary_outcome(member: str, entry: dict[str, Any],
                    achieved_detectable: float | None) -> dict[str, Any]:
    """One of the three fixed §15 outcomes for a primary estimand."""
    if entry.get("status") != "OK":
        return {"member": member, "outcome": "INCONCLUSIVE_NAMED",
                "claim": None, "detail": entry.get("status")}
    interval = entry["simultaneous"]
    estimate = entry["estimate"]
    region = EQUIVALENCE_REGION_PRIMARY
    if interval_excludes_zero(interval) and achieved_detectable is not None \
            and abs(estimate) > achieved_detectable:
        return {"member": member, "outcome": "EFFECT",
                "claim": WORDING_EFFECT, "estimate": estimate,
                "interval": interval}
    if interval_inside(interval, region):
        return {"member": member, "outcome": "EQUIVALENCE",
                "claim": guarded_absence_claim(member, interval, region),
                "estimate": estimate, "interval": interval}
    if not interval_excludes_zero(interval) and \
            (interval[0] < region[0] or interval[1] > region[1]):
        return {"member": member, "outcome": "UNRESOLVED",
                "claim": WORDING_UNRESOLVED, "estimate": estimate,
                "interval": interval,
                "achieved_detectable": achieved_detectable}
    return {"member": member, "outcome": "NO_FIXED_WORDING", "claim": None,
            "estimate": estimate, "interval": interval,
            "detail": "no registered wording matches this configuration; "
                      "reported without claim"}


def exchangeability_holds(f2: dict[str, Any]) -> bool | None:
    """Level-2 licence: all three simultaneous intervals inside ±0.05."""
    if f2.get("status") != "OK":
        return None
    return all(interval_inside(m["simultaneous"],
                               EQUIVALENCE_REGION_EXCHANGEABILITY)
               for m in f2["members"].values())


def terminal_outcome(member: str, outcome: dict[str, Any],
                     exchangeable: bool | None) -> str:
    """The §26 terminal-outcome label for one primary estimand."""
    if outcome["outcome"] == "EFFECT":
        interval = outcome["interval"]
        if interval[0] > SMALLEST_EFFECT_OF_INTEREST:
            return ("POSITIVE_IDENTITY_SPECIFIC_EFFECT" if exchangeable
                    else "POSITIVE_SWAP_EFFECT")
        if interval[1] < -SMALLEST_EFFECT_OF_INTEREST:
            return "NEGATIVE_SWAP_EFFECT"
        return "EFFECT_BELOW_SEI"
    if outcome["outcome"] == "EQUIVALENCE":
        return "EQUIVALENCE"
    if outcome["outcome"] == "UNRESOLVED":
        return "INCONCLUSIVE"
    return outcome["outcome"]
