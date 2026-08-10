"""Profile loading: the CLI-facing successor of the notebook's switch cell.

Three configuration classes are kept apart deliberately:

  A. scientific protocol   ProtocolConfig (built inside stage c112), hashed.
  B. execution environment this module + storage layout + backend choice,
                           recorded in provenance, never hashed into the
                           protocol, never allowed to mutate class A silently.
  C. operational state     dci.pipeline.state, run directories, journals.

`ACTIVE` carries exactly the values the notebook exposed as module-level
switches (MODEL_PROFILE, RUN_MODE, DRY_RUN_MODE, USE_GOOGLE_DRIVE, RUN_ID) plus
the size overrides the headless harness applied through V14_*/V15_* environment
variables. Defaults are byte-identical to the notebook's shipped defaults, so
running with no profile reproduces the notebook's first execution.
"""
from __future__ import annotations

import dataclasses
import tomllib
from pathlib import Path
from typing import Any, Optional


@dataclasses.dataclass
class ActiveConfig:
    # --- notebook switches (defaults identical to the notebook) -------------
    model_profile: str = "dev_fast"
    run_mode: str = "smoke"
    dry_run_mode: bool = True
    use_google_drive: bool = True          # kept name: durable-mirror on/off
    run_id: Optional[str] = None
    # --- execution environment (class B) ------------------------------------
    data_root: Optional[str] = None        # maps to drive_root/local_root
    backend: Optional[str] = None          # None -> CFG.engine / dry-run oracle
    device_index: Optional[int] = None     # overrides CFG.single_gpu_index
    shard_index: Optional[int] = None      # deterministic batch sharding
    shard_total: Optional[int] = None
    # --- protocol-field overrides (the successor of the V14_*/V15_* envs) ----
    # Applied as ProtocolConfig kwargs. Anything here that is scientific is
    # visible in the protocol hash exactly as it was in the notebook.
    protocol_overrides: dict[str, Any] = dataclasses.field(default_factory=dict)
    # provenance
    profile_path: Optional[str] = None

    def storage_overrides(self) -> dict[str, Any]:
        if not self.data_root:
            return {}
        root = Path(self.data_root).expanduser().resolve()
        return {"drive_root": str(root / "durable"),
                "local_root": str(root / "local")}


ACTIVE = ActiveConfig()


def load_profile(path: str | Path) -> ActiveConfig:
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    known = {f.name for f in dataclasses.fields(ActiveConfig)}
    unknown = set(raw) - known
    if unknown:
        raise KeyError(f"unknown profile keys {sorted(unknown)} in {path}; "
                       f"known keys: {sorted(known)}")
    cfg = ActiveConfig(**raw)
    cfg.profile_path = str(path)
    return cfg


def activate(cfg: ActiveConfig) -> None:
    global ACTIVE
    ACTIVE = cfg
