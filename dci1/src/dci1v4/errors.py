"""Errors raised by the v4 implementation.

Every one of these is a fail-closed condition: the run stops rather than
producing an artifact whose meaning is uncertain. Scientific *outcomes*
(terminal statuses, identification statuses) are values recorded on records,
not exceptions — see ``dci1v4.protocol.constants``.
"""
from __future__ import annotations


class ProtocolError(ValueError):
    """A request outside the registered protocol."""


class InstrumentError(ProtocolError):
    """A constraint, severity, or scoring request outside the v4 register."""


class IntegrityError(RuntimeError):
    """Provenance, hashing, storage, or state-machine integrity failed."""


class CarryOverMismatch(IntegrityError):
    """A carried source is not byte-identical to its v3 artifact (§10.2)."""


class VerifierBindingError(IntegrityError):
    """The current verifier hash differs from the frozen one (§10.6)."""


class ProvenanceGuardError(IntegrityError):
    """An analysis input is not a registered v4 artifact (§14.2, §26)."""


class ClaimError(ProtocolError):
    """A claim emitter was asked for a statement it does not license."""


class TerminalStatus(RuntimeError):
    """A registered terminal status was reached (§28.3).

    Carries the status name and the terminal record; the caller writes the
    record and stops the replication.
    """

    def __init__(self, status: str, record: dict):
        super().__init__(f"{status}: replication stops")
        self.status = status
        self.record = record
