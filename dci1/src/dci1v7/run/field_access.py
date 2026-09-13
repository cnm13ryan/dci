"""Which stage actually read which field of which upstream record.

``run/contracts.py`` declares the producer/consumer graph and audited it
against declarations. That audit reported *98 fields, 0 defects* while
``n_checked_against_payloads`` was 0 and Gate 2 was reading ``carried_set``
where §12.7 registers ``calibration_priority``: a declaration is not a read,
and a field being *present* on the producer's record is not evidence that the
consumer consumed it.

So consumption is observed instead of declared. ``read_stage_record`` returns
a mapping that records every key a stage looks at while its payload is being
computed, and the audit compares the observed graph against the declared one.
Two defect kinds only this can find:

``DECLARED_READER_DID_NOT_READ``
    the contract says stage X reads field f, both stages ran, and X never
    looked at f. Either the declaration is wrong or the rule is not on the
    path.

``UNDECLARED_READ``
    stage X read field f of an upstream record and the contract does not
    declare it. This is the shape of V5-E6: the runner reaches for a
    neighbouring field, and nothing says it may.

**Recording is off unless a harness turns it on**, and the tracked mapping is
a ``dict`` subclass that changes no value, so a registered run behaves
identically whether or not anything is watching.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Mapping

__all__ = ["TrackedRecord", "track", "reading_for", "recording",
           "observed", "is_recording"]

#: reader stage -> producing artifact -> set of field names read.
_OBSERVED: dict[str, dict[str, set[str]]] = {}
_ACTIVE = False
_READER: str | None = None


class TrackedRecord(dict):
    """A stage record that remembers which of its keys were looked at.

    Every mapping operation returns exactly what ``dict`` returns. The only
    difference is the note it leaves behind, which is why it is safe on the
    registered path.
    """

    __slots__ = ("_artifact",)

    def __init__(self, artifact: str, data: Mapping[str, Any]):
        super().__init__(data)
        self._artifact = artifact

    def _note(self, key: Any) -> None:
        if not _ACTIVE or _READER is None or not isinstance(key, str):
            return
        _OBSERVED.setdefault(_READER, {}).setdefault(
            self._artifact, set()).add(key)

    def __getitem__(self, key: Any) -> Any:
        self._note(key)
        return super().__getitem__(key)

    def get(self, key: Any, default: Any = None) -> Any:
        self._note(key)
        return super().get(key, default)

    def __contains__(self, key: Any) -> bool:
        self._note(key)
        return super().__contains__(key)


def track(artifact: str, payload: Mapping[str, Any]) -> Any:
    """Wrap a stage record for observation, or hand it back untouched."""
    if not _ACTIVE or isinstance(payload, TrackedRecord):
        return payload
    return TrackedRecord(artifact, payload)


@contextmanager
def reading_for(stage: str) -> Iterator[None]:
    """Attribute every record read inside this block to ``stage``."""
    global _READER
    previous = _READER
    _READER = stage
    try:
        yield
    finally:
        _READER = previous


@contextmanager
def recording() -> Iterator[dict[str, dict[str, set[str]]]]:
    """Observe field reads for the duration of the block."""
    global _ACTIVE
    _OBSERVED.clear()
    _ACTIVE = True
    try:
        yield _OBSERVED
    finally:
        _ACTIVE = False


def is_recording() -> bool:
    return _ACTIVE


def observed() -> dict[str, dict[str, list[str]]]:
    """The observed graph, as plain sorted data."""
    return {reader: {artifact: sorted(fields)
                     for artifact, fields in sorted(by_artifact.items())}
            for reader, by_artifact in sorted(_OBSERVED.items())}
