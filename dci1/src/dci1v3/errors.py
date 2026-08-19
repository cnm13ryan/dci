"""Fail-closed error vocabulary for the v3 implementation."""
from __future__ import annotations


class V3Error(Exception):
    """Base class: any registered v3 rule violated. Always fail closed."""


class ProtocolError(V3Error):
    """A registered scientific rule (preregistration v3) would be violated."""


class IntegrityError(V3Error):
    """An execution-integrity rule (prereg §27) would be violated."""


class StateError(V3Error):
    """An illegal stage transition or predecessor verification failure."""


class CustodyError(V3Error):
    """A masking/unmasking custody rule would be violated."""


class TerminalStatus(V3Error):
    """A registered pre-confirmatory terminal outcome was reached.

    Carries the closed-vocabulary status name and the terminal payload the
    reporting stage persists (prereg §26).
    """

    def __init__(self, status: str, payload: dict | None = None):
        super().__init__(status)
        self.status = status
        self.payload = payload or {}
