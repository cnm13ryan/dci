"""Cross-process writer serialization (item 9).

At most one writer holds mutation authority for a given (study, model
replication, operation). ``flock`` on a per-key lock file provides the
cross-process exclusivity; a second concurrent attempt fails before any
mutation rather than blocking, so duplicate cached draws, duplicate
transitions, replacement manifests, replacement mask keys, and duplicate
unmask events are impossible by construction. Process-local mutexes are
never used for writer authority.
"""
from __future__ import annotations

import fcntl
import os
from pathlib import Path

from dci1v3.errors import IntegrityError


class WriterLock:
    """Exclusive cross-process lock; non-blocking, fail-closed."""

    def __init__(self, lock_dir: Path, study_id: str, model_key: str,
                 operation: str):
        safe = f"{study_id}--{model_key}--{operation}".replace("/", "_")
        self.path = Path(lock_dir) / f"{safe}.lock"
        self._handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a+")
        try:
            fcntl.flock(self._handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self._handle.close()
            self._handle = None
            raise IntegrityError(
                f"writer lock {self.path.name} is held by another process; "
                f"concurrent mutation refused before any write") from error
        self._handle.seek(0)
        self._handle.truncate()
        self._handle.write(str(os.getpid()))
        self._handle.flush()
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None
