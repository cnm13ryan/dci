"""The fixed twenty-response set for the wording-equivalence check (D21).

Prereg §5: the four wordings of each constraint are verified to produce
identical verifier behaviour on a fixed set of twenty test responses. The set
is frozen here, before calibration, and covers passes, failures and boundary
shapes for every rule family in the pool.
"""
from __future__ import annotations

WORDING_CHECK_RESPONSES: tuple[str, ...] = (
    "",
    "   \n\t  ",
    "However, rain falls in many places.",
    "however however however",
    "HOWEVER the plan went ahead.",
    "The trip was fun. A dog ran by.",
    "Most people enjoy warm weather during long summers.",
    "big bold buildings block the breeze",
    "cold coffee cools quickly",
    "fresh fruit feels fine",
    "many mild mornings",
    "polar penguins parade proudly",
    "salty seas surround small islands",
    "tall trees tower today",
    "It rained heavily and steadily, truly a soggy day.",
    "Running, jumping and singing keep everyone smiling.",
    "A sudden puddle appeared by the small green door.",
    "I go to a zoo.",
    "Extraordinary circumstances necessitate comprehensive deliberation.",
    "The word how-ever is hyphenated here, and 'however' is quoted there.",
)
