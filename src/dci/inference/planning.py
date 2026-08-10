"""The backend that cannot generate.

A command advertised as planning-only must be structurally incapable of real
generation, not merely arranged to stop before the first stage that would
generate. Arrangements drift: a stage boundary moves, a gate gains a
micro-generation self-test, an `--until` is passed by hand, and the command
that promised to spend nothing spends GPU budget - or worse, emits synthetic
output into a run directory that later reads as evidence.

This backend satisfies the InferenceBackend contract and refuses every call
that would produce a token. It is selected by `ACTIVE.planning_only`, so the
refusal holds however far through the stage graph the caller travels.
"""
from __future__ import annotations

from typing import Any


class PlanningModeViolation(RuntimeError):
    """Something tried to generate under a planning-only command."""


class PlanningBackend:
    """Answers structural questions; refuses to produce tokens."""

    name = "planning_no_generation"

    def load_model(self):
        raise PlanningModeViolation(
            "planning mode refused to load the inference model. A planning "
            "command inspects the frozen configuration and the design; it does "
            "not hold weights. Use the explicit pre-confirmatory command for "
            "work that must generate.")

    def free_model(self) -> None:
        return None                     # nothing was ever held

    @property
    def tokenizer(self):
        raise PlanningModeViolation(
            "planning mode has no tokenizer: loading one is part of the "
            "execution condition, and its identity belongs to a real run.")

    def generate(self, batch_rows: list[dict[str, Any]],
                 batch_seed: int) -> tuple[list[str], dict[str, Any]]:
        raise PlanningModeViolation(
            f"planning mode refused to generate {len(batch_rows)} row(s) at "
            f"seed {batch_seed}. This is the structural guarantee behind a "
            "planning-only command: reaching a generation call is a bug in the "
            "stage boundary, and it fails loudly here rather than quietly "
            "spending inference budget or writing output that could be "
            "mistaken for evidence.")
