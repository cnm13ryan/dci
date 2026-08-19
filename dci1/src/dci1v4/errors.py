"""Errors raised by the v4 instrument layer."""
from __future__ import annotations


class InstrumentError(ValueError):
    """A constraint, severity, or scoring request outside the v4 register."""


class CarryOverMismatch(RuntimeError):
    """A carried source is not byte-identical to its v3 artifact (§10.2)."""
